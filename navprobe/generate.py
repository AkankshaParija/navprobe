"""Generate the NavProbe task set.

    python -m navprobe.generate --out outputs --per-family 100 --seed 0

Every task passes three checks before it is kept:
  1. ambiguity margins (inside each family's answer())
  2. pixel round-trip: decode(render(scene)) must equal the scene exactly
  3. the answer recomputed from the decoded scene must equal the generator's answer
Rejected candidates are counted by reason in generation_report.json.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from . import __version__
from .decode import decode, same_scene
from .families import FAMILIES
from .render import LEGEND, MARKER_LEGEND, render

SIZES = (20, 28, 36)          # difficulty: small / medium / large maps
EASY_SIZES = (14,)            # easy tier: 2-4 rooms, appended after the standard tier
STYLES = ("plan", "ros")
TWIN_EVERY = 4                # every 4th base task also gets a style twin


def build_prompt(family, scene, style):
    opts = " or ".join(f'"{c}"' for c in family.choices)
    if family.answer_format == "integer":
        opts = "an integer"
    return (
        f"This image is a top-down map of a hospital floor for a delivery robot. Legend: {LEGEND[style]}. "
        f"{MARKER_LEGEND}\n\nQuestion: {family.question(scene)}\n\n"
        f'Reply with JSON only, in the form {{"answer": ...}}, where the answer is {opts}.'
    )


def check(family, scene, style):
    """Return (answer, evidence, image) or (None, reason, None)."""
    ans, ev = family.answer(scene)
    if ans is None:
        return None, ev, None
    img = render(scene, style)
    try:
        dec = decode(img, style)
    except ValueError as e:
        return None, f"decode_error:{e}", None
    if not same_scene(scene, dec):
        return None, "roundtrip_mismatch", None
    ans2, _ = family.answer(dec)
    if ans2 != ans:
        return None, "answer_changed_after_decode", None
    return ans, ev, img


def _seed(*parts):
    return int(hashlib.sha256("/".join(map(str, parts)).encode()).hexdigest()[:12], 16)


def generate(out: Path, per_family: int, seed: int, max_tries: int = 400, easy_per_family: int = 0):
    out = Path(out)
    (out / "images").mkdir(parents=True, exist_ok=True)
    tasks, rejects = [], collections.Counter()
    t0 = time.time()

    def emit(tid, fam, scene, style, ans, ev, img, size, base_seed, **extra):
        img.save(out / "images" / f"{tid}.png", optimize=False)
        tasks.append({
            "task_id": tid, "family": fam.name, "style": style, "size": size,
            "prompt": build_prompt(fam, scene, style), "question": fam.question(scene),
            "answer": ans, "choices": list(fam.choices), "answer_format": fam.answer_format,
            "evidence": ev, "image": f"images/{tid}.png", "seed": base_seed,
            "scene": scene.to_json(), "generator_version": __version__, **extra,
        })
        return tid

    def run_tier(fam, sizes, n, tier):
        made = 0
        # small easy maps rarely have a room with 4 doorways, so balance F1 over 1-3 there
        targets = fam.choices if tier == "standard" or fam.name != "F1_count_doors" else ("1", "2", "3")
        for k in range(n * 3):
            if made >= n:
                break
            L = len(targets)
            target = targets[k % L]                       # cycles every L
            want_trap = (k // L) % 2 == 0                 # cycles every 2L (only used by F5)
            style = STYLES[(k // (2 * L)) % 2]            # cycles every 4L: independent of answer and trap
            size = sizes[(k // (4 * L)) % len(sizes)]     # independent of answer, trap and style
            for attempt in range(max_tries):
                s_seed = _seed(seed, tier, fam.name, k, attempt)
                rng = np.random.default_rng(s_seed)
                scene = fam.sample(rng, size)
                if scene is None:
                    rejects[(fam.name, "no_free_space")] += 1
                    continue
                ans, ev, img = check(fam, scene, style)
                if ans is None:
                    rejects[(fam.name, ev)] += 1
                    continue
                if ans != target:
                    rejects[(fam.name, "balancing_skip")] += 1
                    continue
                if fam.name.startswith("F5") and ev["trap"] != want_trap:
                    rejects[(fam.name, "balancing_skip")] += 1
                    continue
                # stable IDs: family + tier + schedule slot, so one family never shifts another's IDs
                base = emit(f"{fam.name.split('_')[0]}-{tier[0]}{k:04d}", fam, scene, style, ans, ev, img,
                            size, s_seed, tier=tier)
                made += 1
                # minimal pair: one change that flips the answer
                partner = fam.pair(scene, rng)
                if partner is not None:
                    p_ans, p_ev, p_img = check(fam, partner, style)
                    if p_ans is not None and p_ans != ans:
                        pid = f"P-{base}"
                        tasks[-1]["pair_id"] = pid
                        emit(base + "P", fam, partner, style, p_ans, p_ev, p_img, size, s_seed, tier=tier,
                             pair_id=pid, pair_role="partner")
                    else:
                        rejects[(fam.name, "pair_not_flipping")] += 1
                # style twin: identical scene and question in the other style
                if made % TWIN_EVERY == 0:
                    other = STYLES[1 - STYLES.index(style)]
                    t_ans, t_ev, t_img = check(fam, scene, other)
                    if t_ans == ans:
                        wid = f"W-{base}"
                        tasks[[t["task_id"] for t in tasks].index(base)]["twin_id"] = wid
                        emit(base + "W", fam, scene, other, t_ans, t_ev, t_img, size, s_seed, tier=tier,
                             twin_id=wid, twin_role="twin")
                break
            else:
                rejects[(fam.name, "target_not_found")] += 1
        print(f"{fam.name} [{tier}]: {made} base tasks", flush=True)

    # Standard tier first, then the easy tier.
    for fam in FAMILIES:
        run_tier(fam, SIZES, per_family, "standard")
    if easy_per_family:
        for fam in FAMILIES:
            run_tier(fam, EASY_SIZES, easy_per_family, "easy")

    with open(out / "tasks.jsonl", "w") as f:
        for t in tasks:
            f.write(json.dumps(t, sort_keys=True) + "\n")

    report = {
        "generator_version": __version__, "seed": seed, "per_family": per_family,
        "n_tasks": len(tasks), "seconds": round(time.time() - t0, 1),
        "by_family": dict(collections.Counter(t["family"] for t in tasks)),
        "answers": {f.name: dict(collections.Counter(t["answer"] for t in tasks if t["family"] == f.name))
                    for f in FAMILIES},
        "minimal_pairs": sum(1 for t in tasks if t.get("pair_role") == "partner"),
        "style_twins": sum(1 for t in tasks if t.get("twin_role") == "twin"),
        "rejections": {f"{a}:{b}": n for (a, b), n in sorted(rejects.items())},
    }
    (out / "generation_report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    return tasks, report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--per-family", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--easy-per-family", type=int, default=50, help="easy-tier tasks (14x14 maps) per family")
    a = ap.parse_args()
    _, rep = generate(Path(a.out), a.per_family, a.seed, easy_per_family=a.easy_per_family)
    print(json.dumps({k: rep[k] for k in ("n_tasks", "minimal_pairs", "style_twins", "seconds")}, indent=2))


if __name__ == "__main__":
    main()
