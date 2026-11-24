"""Failure gallery: for each family, show tasks most models got wrong, with every model's answer.

    python -m navprobe.gallery --tasks outputs

Writes outputs/results/gallery/<family>.png and gallery.md (used in the slides and the write-up).
"""
from __future__ import annotations

import argparse
import collections
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .report import FAMILY_LABEL

CONTROLS = {"oracle", "random"}
TILE = 420


def _font(size):
    return ImageFont.load_default(size=size)


def build(root: Path, per_family: int = 3):
    scored = root / "results" / "scored.jsonl"
    rows = [json.loads(l) for l in open(scored)]
    tasks = {t["task_id"]: t for t in (json.loads(l) for l in open(root / "tasks.jsonl"))}
    models = sorted({r["model"] for r in rows if r["model"] not in CONTROLS and "__blind" not in r["model"]})
    if not models:
        raise SystemExit("no model results yet: run models, then `python -m navprobe.report` first")
    preds = collections.defaultdict(dict)  # task_id -> model -> pred
    for r in rows:
        if r["model"] in models:
            preds[r["task_id"]][r["model"]] = r["pred"]
    out = root / "results" / "gallery"
    out.mkdir(parents=True, exist_ok=True)
    md = ["# Failure gallery\n", "Tasks that the most models answered wrongly (base tasks only).\n"]
    for fam, label in FAMILY_LABEL.items():
        cands = []
        for tid, p in preds.items():
            t = tasks[tid]
            if t["family"] != fam or t.get("pair_role") or t.get("twin_role") or len(p) < len(models):
                continue
            wrong = sum(v != t["answer"] for v in p.values())
            cands.append((-wrong, tid))
        cands.sort()
        pick = [tid for _, tid in cands[:per_family]]
        if not pick:
            continue
        sheet = Image.new("RGB", (TILE * len(pick), TILE + 230), "white")
        d = ImageDraw.Draw(sheet)
        md.append(f"\n## {label}\n")
        for i, tid in enumerate(pick):
            t = tasks[tid]
            im = Image.open(root / t["image"]).convert("RGB")
            im.thumbnail((TILE - 10, TILE - 10))
            sheet.paste(im, (i * TILE + 5, 5))
            y = TILE + 2
            q = textwrap.fill(t["question"], 62)
            d.text((i * TILE + 6, y), q, fill="black", font=_font(11))
            y += 14 * (q.count("\n") + 1) + 4
            d.text((i * TILE + 6, y), f"correct: {t['answer']}", fill=(0, 120, 0), font=_font(13))
            y += 18
            for m in models:
                v = preds[tid].get(m)
                col = (0, 120, 0) if v == t["answer"] else (190, 0, 0)
                d.text((i * TILE + 6, y), f"{m[:34]}: {v}", fill=col, font=_font(11))
                y += 14
            md.append(f"- **{tid}** ({t['style']}, {t['size']}x{t['size']}): correct **{t['answer']}**; "
                      + ", ".join(f"{m}: {preds[tid].get(m)}" for m in models)
                      + f"; evidence `{json.dumps(t['evidence'])}`")
        sheet.save(out / f"{fam}.png")
    (out / "gallery.md").write_text("\n".join(md) + "\n")
    print(f"gallery written to {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="outputs")
    ap.add_argument("--per-family", type=int, default=3)
    a = ap.parse_args()
    build(Path(a.tasks), a.per_family)


if __name__ == "__main__":
    main()
