"""Human audit: measure how well a person answers a random sample of tasks.

    python -m navprobe.audit build  --tasks outputs              # writes outputs/audit/audit.html
    (open it in a browser, answer all tasks, click "Download answers")
    python -m navprobe.audit ingest --tasks outputs ~/Downloads/navprobe_human_audit.json
    python -m navprobe.report --tasks outputs                     # 'human_audit' row appears

The page is self-contained (images embedded) and contains NO answer key.
The sample is 10 base tasks per family, drawn with a fixed seed.
"""
from __future__ import annotations

import argparse
import base64
import json
import random
from pathlib import Path

PER_FAMILY = 10
SEED = 2026

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>NavProbe human audit</title>
<style>
:root{--bg:#fafaf7;--fg:#1d1d1f;--muted:#6b6b70;--card:#fff;--line:#e3e1da;--accent:#1f5fd6;--btn:#f1efe8}
@media (prefers-color-scheme: dark){:root{--bg:#141416;--fg:#ececef;--muted:#9a9aa2;--card:#1e1e22;--line:#2e2e34;--accent:#6c9cff;--btn:#26262c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.45 -apple-system,system-ui,sans-serif}
main{max-width:980px;margin:0 auto;padding:16px}
header{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
h1{font-size:20px;margin:4px 0}.muted{color:var(--muted);font-size:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-top:12px}
.grid{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:16px}
@media (max-width:760px){.grid{grid-template-columns:1fr}}
img{width:100%;height:auto;border-radius:8px;border:1px solid var(--line);image-rendering:pixelated}
.q{font-weight:600;margin:8px 0 12px}.legend{font-size:13px;color:var(--muted)}
.choices{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
button{font:inherit;padding:10px 16px;border-radius:8px;border:1px solid var(--line);background:var(--btn);color:var(--fg);cursor:pointer}
button:hover{border-color:var(--accent)}button.primary{background:var(--accent);color:#fff;border-color:var(--accent)}
.bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden;margin-top:8px}.bar>div{height:100%;background:var(--accent)}
kbd{border:1px solid var(--line);border-radius:4px;padding:0 4px;font-size:12px}
</style></head><body><main>
<header><h1>NavProbe human audit</h1><span class="muted" id="prog"></span></header>
<div class="bar"><div id="barfill" style="width:0"></div></div>
<div id="app"></div>
</main>
<script>
const TASKS = __TASKS__;
const KEY = "navprobe_audit_v1";
let state = {i:0, answers:{}};
try { const s = JSON.parse(localStorage.getItem(KEY)); if (s && s.answers) state = s; } catch(e) {}
function save(){ try { localStorage.setItem(KEY, JSON.stringify(state)); } catch(e) {} }
let shownAt = Date.now();
function render(){
  const app = document.getElementById("app");
  const done = Object.keys(state.answers).length;
  document.getElementById("prog").textContent = done + " / " + TASKS.length + " answered";
  document.getElementById("barfill").style.width = (100*done/TASKS.length) + "%";
  if (state.i >= TASKS.length) {
    app.innerHTML = `<div class="card"><p><b>All ${TASKS.length} tasks answered.</b> Click below to save your answers,
      then tell Claude where the file went (usually Downloads).</p>
      <button class="primary" id="dl">Download answers</button> <button id="back">Go back</button></div>`;
    document.getElementById("dl").onclick = download;
    document.getElementById("back").onclick = () => { state.i = TASKS.length - 1; save(); render(); };
    return;
  }
  const t = TASKS[state.i];
  const prev = state.answers[t.task_id];
  app.innerHTML = `<div class="card grid"><div><img src="${t.img}" alt="map for task ${t.task_id}"></div>
    <div><div class="muted">Task ${state.i+1} of ${TASKS.length}</div>
    <div class="q">${t.question}</div>
    <div class="legend">${t.legend}</div>
    <div class="choices">${t.choices.map((c,k)=>`<button data-c="${c}" ${prev&&prev.answer===c?'class="primary"':''}>${c} <kbd>${k+1}</kbd></button>`).join("")}</div>
    <p class="muted" style="margin-top:16px">${state.i>0?'<button id="prev">&larr; Previous</button>':''}</p></div></div>`;
  app.querySelectorAll("button[data-c]").forEach(b => b.onclick = () => pick(b.dataset.c));
  const p = document.getElementById("prev"); if (p) p.onclick = () => { state.i--; save(); render(); };
  shownAt = Date.now();
}
function pick(c){
  const t = TASKS[state.i];
  state.answers[t.task_id] = {answer:c, seconds:Math.round((Date.now()-shownAt)/100)/10};
  state.i++; save(); render();
}
document.addEventListener("keydown", e => {
  const t = TASKS[state.i]; if (!t) return;
  const k = parseInt(e.key, 10); if (k >= 1 && k <= t.choices.length) pick(t.choices[k-1]);
});
function download(){
  const blob = new Blob([JSON.stringify({version:1, answers:state.answers}, null, 1)], {type:"application/json"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
  a.download = "navprobe_human_audit.json"; document.body.appendChild(a); a.click(); a.remove();
}
render();
</script></body></html>
"""


def sample(tasks):
    base = [t for t in tasks if not t.get("pair_role") and not t.get("twin_role")]
    rng = random.Random(SEED)
    out = []
    for fam in sorted({t["family"] for t in base}):
        pool = sorted((t for t in base if t["family"] == fam), key=lambda t: t["task_id"])
        out += rng.sample(pool, min(PER_FAMILY, len(pool)))
    rng.shuffle(out)
    return out


def build(root: Path):
    from .render import LEGEND, MARKER_LEGEND
    tasks = [json.loads(l) for l in open(root / "tasks.jsonl")]
    items = []
    for t in sample(tasks):
        img = base64.b64encode((root / t["image"]).read_bytes()).decode()
        items.append({"task_id": t["task_id"], "question": t["question"], "choices": t["choices"],
                      "legend": f"Legend: {LEGEND[t['style']]}. {MARKER_LEGEND}",
                      "img": "data:image/png;base64," + img})  # deliberately no answer field
    out = root / "audit"
    out.mkdir(exist_ok=True)
    (out / "audit.html").write_text(PAGE.replace("__TASKS__", json.dumps(items)))
    (out / "sample_ids.json").write_text(json.dumps([i["task_id"] for i in items], indent=1))
    print(f"wrote {out / 'audit.html'} with {len(items)} tasks (no answer key inside)")


def ingest(root: Path, path: Path):
    data = json.loads(Path(path).expanduser().read_text())["answers"]
    out = root / "responses" / "human_audit.jsonl"
    with open(out, "w") as f:
        for tid, a in sorted(data.items()):
            f.write(json.dumps({"task_id": tid, "model": "human_audit", "blind": False,
                                "raw": json.dumps({"answer": a["answer"]}), "seconds": a.get("seconds")}) + "\n")
    print(f"{len(data)} human answers -> {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["build", "ingest"])
    ap.add_argument("file", nargs="?")
    ap.add_argument("--tasks", default="outputs")
    a = ap.parse_args()
    if a.cmd == "build":
        build(Path(a.tasks))
    else:
        ingest(Path(a.tasks), Path(a.file))


if __name__ == "__main__":
    main()
