"""Independently re-check a generated task set from its PNGs.

    python -m navprobe.verify outputs

For every task: decode the PNG (pixels only), compare with the stored scene,
recompute the answer from the decoded scene, and compare with the stored answer.
Also checks answer balance per family. Writes verification_report.json.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

import numpy as np
from PIL import Image

from .decode import decode, same_scene
from .families import BY_NAME
from .mapgen import Scene


def scene_from_json(d) -> Scene:
    return Scene(np.array(d["grid"], dtype=np.int8), tuple(d["robot"]), d["robot_size"], d["heading"],
                 {k: tuple(v) for k, v in d["goals"].items()})


def verify_task(root: Path, t: dict):
    """Return None if the task is valid, else a short failure reason."""
    fam = BY_NAME.get(t["family"])
    if fam is None:
        return "unknown_family"
    if t["answer"] not in fam.choices:
        return "answer_not_in_choices"
    try:
        dec = decode(Image.open(root / t["image"]), t["style"])
    except Exception as e:  # noqa: BLE001
        return f"decode_error:{e}"
    if not same_scene(dec, scene_from_json(t["scene"])):
        return "image_does_not_match_scene"
    ans, _ = fam.answer(dec)
    if ans is None:
        return "ambiguous_from_image"
    if ans != t["answer"]:
        return "answer_key_wrong"
    return None


def verify(root: Path):
    root = Path(root)
    tasks = [json.loads(l) for l in open(root / "tasks.jsonl")]
    failures = {}
    for t in tasks:
        why = verify_task(root, t)
        if why:
            failures[t["task_id"]] = why
    base = [t for t in tasks if not t.get("pair_role") and not t.get("twin_role")]
    balance = {}
    for fam in sorted({t["family"] for t in base}):
        cnt = collections.Counter(t["answer"] for t in base if t["family"] == fam)
        balance[fam] = {"counts": dict(cnt), "max_share": round(max(cnt.values()) / sum(cnt.values()), 3)}
    ids = [t["task_id"] for t in tasks]
    rep = {
        "n_tasks": len(tasks), "n_valid": len(tasks) - len(failures), "failures": failures,
        "duplicate_ids": len(ids) - len(set(ids)),
        "answer_balance_base_tasks": balance,
    }
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="outputs")
    a = ap.parse_args()
    rep = verify(Path(a.root))
    (Path(a.root) / "verification_report.json").write_text(json.dumps(rep, indent=2, sort_keys=True))
    print(f"{rep['n_valid']}/{rep['n_tasks']} tasks verified from pixels; {len(rep['failures'])} failures")
    raise SystemExit(1 if rep["failures"] else 0)


if __name__ == "__main__":
    main()
