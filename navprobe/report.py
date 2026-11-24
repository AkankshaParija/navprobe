"""Score every cached response file and build the findings report.

    python -m navprobe.report --tasks outputs

Scoring is exact match after strict parsing of {"answer": ...}. A reply that cannot be
parsed counts as wrong and is reported separately as 'invalid'.
Headline accuracy uses base tasks only (balanced answers); minimal pairs and style twins
are reported as separate consistency metrics.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

import numpy as np

FAMILY_LABEL = {
    "F1_count_doors": "F1 count doors", "F2_direction": "F2 left/right",
    "F3_reachability": "F3 reachable?", "F4_fit": "F4 fits?",
    "F5_nearest_by_path": "F5 nearest by path", "F6_line_of_sight": "F6 line of sight",
}


def parse_answer(raw: str, choices):
    """Return the canonical choice, or None if the reply is invalid."""
    if raw is None:
        return None
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.S)
    m = None
    for m in re.finditer(r"\{[^{}]*\"answer\"[^{}]*\}", raw, re.S):
        pass  # keep the last JSON object
    if not m:
        return None
    try:
        val = json.loads(m.group(0))["answer"]
    except (json.JSONDecodeError, KeyError):
        return None
    v = str(val).strip().strip(".\"' ").lower()
    if isinstance(val, (int, float)) or re.fullmatch(r"-?\d+(\.0+)?", v):
        try:
            v = str(int(float(v)))
        except ValueError:
            pass
    lut = {c.lower(): c for c in choices}
    return lut.get(v)


def bootstrap_ci(x, n=2000, seed=0):
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = rng.choice(x, size=(n, len(x)), replace=True).mean(1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def score_model(tasks, responses):
    by_id = {t["task_id"]: t for t in tasks}
    rows = []
    for r in responses:
        t = by_id.get(r["task_id"])
        if t is None:
            continue
        pred = parse_answer(r["raw"], t["choices"])
        rows.append({**{k: t.get(k) for k in ("task_id", "family", "size", "style", "answer", "pair_id",
                                               "pair_role", "twin_id", "twin_role")},
                     "pred": pred, "valid": pred is not None, "correct": pred == t["answer"],
                     "trap": t["evidence"].get("trap"), "raw": r["raw"]})
    return rows


def summarize(rows, tasks):
    base = [r for r in rows if not r["pair_role"] and not r["twin_role"]]
    out = {"n_scored": len(rows), "n_base": len(base)}
    acc = [r["correct"] for r in base]
    out["accuracy"] = float(np.mean(acc)) if acc else None
    out["ci95"] = bootstrap_ci(acc)
    out["invalid_rate"] = float(np.mean([not r["valid"] for r in rows])) if rows else None
    answered = [r["correct"] for r in base if r["valid"]]
    out["accuracy_on_answered"] = float(np.mean(answered)) if answered else None  # ignores replies with no answer
    fam = {}
    for f in FAMILY_LABEL:
        xs = [r["correct"] for r in base if r["family"] == f]
        if xs:
            fam[f] = {"n": len(xs), "acc": float(np.mean(xs)), "ci95": bootstrap_ci(xs)}
    out["by_family"] = fam
    # answer collapse: share of the single most frequent prediction per family (true answers are balanced,
    # so a model that looks at the image should spread its answers; 1.0 = always the same answer)
    coll = {}
    for f in FAMILY_LABEL:
        ps = [r["pred"] for r in base if r["family"] == f]
        if ps:
            coll[f] = max(collections.Counter(ps).values()) / len(ps)
    out["answer_collapse"] = coll
    out["mean_answer_collapse"] = float(np.mean(list(coll.values()))) if coll else None
    out["by_size"] = {str(s): float(np.mean([r["correct"] for r in base if r["size"] == s]))
                      for s in sorted({r["size"] for r in base})}
    f5 = [r for r in base if r["family"] == "F5_nearest_by_path"]
    if f5:
        out["F5_trap"] = {
            "trap_acc": float(np.mean([r["correct"] for r in f5 if r["trap"]] or [np.nan])),
            "no_trap_acc": float(np.mean([r["correct"] for r in f5 if not r["trap"]] or [np.nan])),
        }
    # minimal pairs: both members correct
    by_pair = collections.defaultdict(list)
    for r in rows:
        if r["pair_id"]:
            by_pair[r["pair_id"]].append(r["correct"])
    full = [all(v) for v in by_pair.values() if len(v) == 2]
    out["pair_consistency"] = float(np.mean(full)) if full else None
    out["n_pairs"] = len(full)
    # style twins: same answer in both styles
    by_twin = collections.defaultdict(list)
    for r in rows:
        if r["twin_id"]:
            by_twin[r["twin_id"]].append(r["pred"])
    tw = [v[0] == v[1] for v in by_twin.values() if len(v) == 2]
    out["style_agreement"] = float(np.mean(tw)) if tw else None
    out["n_twins"] = len(tw)
    return out


def chance_by_family(tasks):
    return {f: 1.0 / len(next(t["choices"] for t in tasks if t["family"] == f))
            for f in FAMILY_LABEL if any(t["family"] == f for t in tasks)}


def make_figures(summaries, chance, fig_dir: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_dir.mkdir(parents=True, exist_ok=True)
    models = list(summaries)
    fams = [f for f in FAMILY_LABEL if f in chance]
    # 1. accuracy by family
    fig, ax = plt.subplots(figsize=(11, 4.5))
    w = 0.8 / max(len(models), 1)
    for i, m in enumerate(models):
        ys = [summaries[m]["by_family"].get(f, {}).get("acc", np.nan) for f in fams]
        lo = [ys[j] - summaries[m]["by_family"].get(f, {}).get("ci95", (np.nan,) * 2)[0] for j, f in enumerate(fams)]
        hi = [summaries[m]["by_family"].get(f, {}).get("ci95", (np.nan,) * 2)[1] - ys[j] for j, f in enumerate(fams)]
        ax.bar(np.arange(len(fams)) + i * w, ys, w, yerr=[lo, hi], capsize=2, label=m)
    for j, f in enumerate(fams):
        ax.hlines(chance[f], j - 0.1, j + 0.8, colors="k", linestyles="dashed", linewidth=1)
    ax.set_xticks(np.arange(len(fams)) + 0.4 - w / 2)
    ax.set_xticklabels([FAMILY_LABEL[f] for f in fams], fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("accuracy (base tasks, 95% CI)")
    ax.set_title("Accuracy by reasoning family (dashed = chance)")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(fig_dir / "accuracy_by_family.png", dpi=150)
    plt.close(fig)
    # 2. accuracy vs map size
    fig, ax = plt.subplots(figsize=(6, 4))
    for m in models:
        s = summaries[m]["by_size"]
        ax.plot([int(k) for k in s], list(s.values()), marker="o", label=m)
    ax.set_xlabel("map size (cells per side)")
    ax.set_ylabel("accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_title("Accuracy as maps get larger")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "accuracy_by_size.png", dpi=150)
    plt.close(fig)
    # 3. F5 trap
    ms = [m for m in models if "F5_trap" in summaries[m]]
    if ms:
        fig, ax = plt.subplots(figsize=(7, 4))
        x = np.arange(len(ms))
        ax.bar(x - 0.2, [summaries[m]["F5_trap"]["no_trap_acc"] for m in ms], 0.4, label="looks-nearest = nearest")
        ax.bar(x + 0.2, [summaries[m]["F5_trap"]["trap_acc"] for m in ms], 0.4, label="trap: looks-nearest is wrong")
        ax.axhline(1 / 3, color="k", linestyle="dashed", linewidth=1)
        ax.set_xticks(x)
        ax.set_xticklabels(ms, rotation=20, ha="right", fontsize=8)
        ax.set_ylim(0, 1.05)
        ax.set_title("F5: do models plan, or eyeball straight-line distance?")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(fig_dir / "f5_trap.png", dpi=150)
        plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="outputs")
    a = ap.parse_args()
    root = Path(a.tasks)
    tasks = [json.loads(l) for l in open(root / "tasks.jsonl")]
    chance = chance_by_family(tasks)
    summaries, all_rows = {}, {}
    for f in sorted((root / "responses").glob("*.jsonl")):
        if f.name.startswith("."):  # skip macOS metadata files such as ._oracle.jsonl
            continue
        resp = [json.loads(l) for l in open(f)]
        rows = score_model(tasks, resp)
        summaries[f.stem] = summarize(rows, tasks)
        all_rows[f.stem] = rows
    res = root / "results"
    res.mkdir(exist_ok=True)
    (res / "summary.json").write_text(json.dumps({"chance": chance, "models": summaries}, indent=2))
    with open(res / "scored.jsonl", "w") as fh:
        for m, rows in all_rows.items():
            for r in rows:
                fh.write(json.dumps({"model": m, **{k: v for k, v in r.items() if k != "raw"}}) + "\n")
    if summaries:
        make_figures(summaries, chance, res / "figures")
    # console table
    fams = list(chance)
    print(f"{'model':42s} {'all':>6s} " + " ".join(f"{f[:2]:>5s}" for f in fams)
          + "  pairs  twins invalid collapse")
    for m, s in summaries.items():
        cells = " ".join(f"{s['by_family'].get(f, {}).get('acc', float('nan')):5.2f}" for f in fams)
        pc = s["pair_consistency"]
        sa = s["style_agreement"]
        print(f"{m:42s} {s['accuracy']:6.3f} {cells}  {pc if pc is None else round(pc, 2)!s:>5}"
              f"  {sa if sa is None else round(sa, 2)!s:>5} {s['invalid_rate']:6.3f}"
              f"   {s['mean_answer_collapse']:5.2f}")
    print("chance" + " " * 43 + " ".join(f"{chance[f]:5.2f}" for f in fams))


if __name__ == "__main__":
    main()
