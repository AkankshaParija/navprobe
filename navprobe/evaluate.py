"""Run an agent on the task set and cache every raw response.

    python -m navprobe.evaluate --tasks outputs --model oracle
    python -m navprobe.evaluate --tasks outputs --model random
    python -m navprobe.evaluate --tasks outputs --model vllm:Qwen/Qwen2.5-VL-7B-Instruct          # GPU (HPC)
    python -m navprobe.evaluate --tasks outputs --model vllm:Qwen/Qwen2.5-VL-7B-Instruct --blind  # no image
    python -m navprobe.evaluate --tasks outputs --model hf:Qwen/Qwen2.5-VL-3B-Instruct            # transformers fallback
    GEMINI_API_KEY=... python -m navprobe.evaluate --tasks outputs --model gemini:gemini-2.5-flash

Responses are appended to outputs/responses/<model>.jsonl as soon as they arrive,
so an interrupted run (e.g. a Slurm time limit) resumes where it stopped.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import random
import re
import time
from pathlib import Path

BLIND_NOTE = "(You are not given the image. Answer with your best guess.)\n\n"
MAX_NEW_TOKENS = 256


def slug(model: str, blind: bool) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", model)
    return s + ("__blind" if blind else "")


def load_tasks(root: Path):
    return [json.loads(l) for l in open(root / "tasks.jsonl")]


def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


# ---------------------------------------------------------------- agents

class Oracle:
    """Reads the answer key. Must score 100%: proves the scorer accepts correct answers."""
    def run(self, batch, root, blind):
        return [json.dumps({"answer": t["answer"]}) for t in batch]


class RandomAgent:
    """Uniform random choice. Should score at chance: proves the scorer rejects guessing."""
    def __init__(self, seed=0):
        self.rng = random.Random(seed)

    def run(self, batch, root, blind):
        return [json.dumps({"answer": self.rng.choice(t["choices"])}) for t in batch]


class VLLMAgent:
    def __init__(self, model_id):
        from vllm import LLM, SamplingParams
        self.llm = LLM(model=model_id, max_model_len=8192, limit_mm_per_prompt={"image": 1},
                       trust_remote_code=True, seed=0)
        self.params = SamplingParams(temperature=0.0, max_tokens=MAX_NEW_TOKENS, seed=0)

    def run(self, batch, root, blind):
        convs = []
        for t in batch:
            if blind:
                content = [{"type": "text", "text": BLIND_NOTE + t["prompt"]}]
            else:
                url = "data:image/png;base64," + _b64(root / t["image"])
                content = [{"type": "image_url", "image_url": {"url": url}}, {"type": "text", "text": t["prompt"]}]
            convs.append([{"role": "user", "content": content}])
        outs = self.llm.chat(convs, self.params, use_tqdm=False)
        return [o.outputs[0].text for o in outs]


class HFAgent:
    """transformers fallback (slower, one task at a time)."""
    def __init__(self, model_id):
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor
        self.torch = torch
        self.proc = AutoProcessor.from_pretrained(model_id)
        self.model = AutoModelForImageTextToText.from_pretrained(model_id, torch_dtype=torch.bfloat16,
                                                                 device_map="auto")

    def run(self, batch, root, blind):
        from PIL import Image
        outs = []
        for t in batch:
            content = [] if blind else [{"type": "image", "image": Image.open(root / t["image"]).convert("RGB")}]
            content.append({"type": "text", "text": (BLIND_NOTE if blind else "") + t["prompt"]})
            msgs = [{"role": "user", "content": content}]
            inputs = self.proc.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True,
                                                   return_dict=True, return_tensors="pt").to(self.model.device)
            with self.torch.no_grad():
                gen = self.model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False)
            outs.append(self.proc.decode(gen[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True))
        return outs


class GeminiAgent:
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"

    def __init__(self, model_id, min_interval=4.5):
        import requests
        self.requests = requests
        self.model = model_id
        self.key = os.environ["GEMINI_API_KEY"]
        self.min_interval = min_interval  # stay under free-tier requests-per-minute
        self.last = 0.0

    def _call(self, parts):
        body = {"contents": [{"parts": parts}], "generationConfig": {"temperature": 0}}
        for attempt in range(8):
            wait = self.min_interval - (time.time() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            r = self.requests.post(self.URL.format(m=self.model), json=body, timeout=120,
                                   headers={"x-goog-api-key": self.key})
            if r.status_code == 200:
                cand = r.json().get("candidates", [{}])[0]
                return "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
            if r.status_code in (429, 500, 503):
                time.sleep(min(60, 5 * 2 ** attempt))
                continue
            raise RuntimeError(f"Gemini API error {r.status_code}: {r.text[:300]}")
        raise RuntimeError("Gemini API: too many retries")

    def run(self, batch, root, blind):
        outs = []
        for t in batch:
            parts = [] if blind else [{"inline_data": {"mime_type": "image/png", "data": _b64(root / t["image"])}}]
            parts.append({"text": (BLIND_NOTE if blind else "") + t["prompt"]})
            outs.append(self._call(parts))
        return outs


def make_agent(spec: str):
    if spec == "oracle":
        return Oracle(), 64
    if spec == "random":
        return RandomAgent(), 64
    kind, _, model_id = spec.partition(":")
    if kind == "vllm":
        return VLLMAgent(model_id), 64
    if kind == "hf":
        return HFAgent(model_id), 1
    if kind == "gemini":
        return GeminiAgent(model_id), 1
    raise SystemExit(f"unknown model spec {spec!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", default="outputs")
    ap.add_argument("--model", required=True)
    ap.add_argument("--blind", action="store_true", help="send the question without the image")
    ap.add_argument("--limit", type=int, default=0, help="only the first N tasks (smoke test)")
    ap.add_argument("--base-only", action="store_true", help="skip minimal-pair partners and style twins")
    a = ap.parse_args()

    root = Path(a.tasks)
    tasks = load_tasks(root)
    if a.base_only:
        tasks = [t for t in tasks if not t.get("pair_role") and not t.get("twin_role")]
    if a.limit:
        tasks = tasks[: a.limit]
    out = root / "responses" / f"{slug(a.model, a.blind)}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        done = {json.loads(l)["task_id"] for l in open(out)}
    todo = [t for t in tasks if t["task_id"] not in done]
    print(f"{a.model}{' (blind)' if a.blind else ''}: {len(done)} cached, {len(todo)} to run", flush=True)
    if not todo:
        return
    agent, bs = make_agent(a.model)
    with open(out, "a") as f:
        for i in range(0, len(todo), bs):
            batch = todo[i:i + bs]
            t0 = time.time()
            raws = agent.run(batch, root, a.blind)
            dt = (time.time() - t0) / len(batch)
            for t, raw in zip(batch, raws):
                f.write(json.dumps({"task_id": t["task_id"], "model": a.model, "blind": a.blind,
                                    "raw": raw, "seconds": round(dt, 3)}) + "\n")
            f.flush()
            print(f"  {min(i + bs, len(todo))}/{len(todo)}", flush=True)


if __name__ == "__main__":
    main()
