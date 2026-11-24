"""Round-trip, determinism, verification and mutation tests on a small generated set."""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

from navprobe.decode import decode, same_scene
from navprobe.generate import generate
from navprobe.mapgen import MapParams, generate_layout, place_markers
from navprobe.render import CELL, STYLES, render
from navprobe.verify import verify, verify_task


@pytest.fixture(scope="session")
def small_set(tmp_path_factory):
    out = tmp_path_factory.mktemp("gen")
    generate(out, per_family=4, seed=123)
    return out


def _digest(root: Path):
    h = hashlib.sha256()
    h.update((root / "tasks.jsonl").read_bytes())
    for p in sorted((root / "images").glob("*.png")):
        h.update(p.read_bytes())
    return h.hexdigest()


def test_roundtrip_many_maps():
    for s in range(60):
        rng = np.random.default_rng(s)
        g, _ = generate_layout(rng, MapParams(size=[20, 28, 36][s % 3], close_prob=0.2))
        sc = place_markers(rng, g, robot_size=1 + s % 2, n_goals=3)
        for style in STYLES:
            assert same_scene(sc, decode(render(sc, style), style))


def test_generated_set_verifies(small_set):
    rep = verify(small_set)
    assert rep["failures"] == {}
    assert rep["n_tasks"] >= 24
    assert rep["duplicate_ids"] == 0


def test_deterministic(small_set, tmp_path):
    generate(tmp_path, per_family=4, seed=123)
    assert _digest(tmp_path) == _digest(small_set)


# ---------------------------------------------------------------- mutation tests
# Each mutation deliberately breaks a valid task. The verifier must flag every one.

def _load(root):
    return [json.loads(l) for l in open(root / "tasks.jsonl")]


def _copy(root, tmp):
    dst = tmp / "mut"
    shutil.copytree(root, dst)
    return dst


def _paint_cell(img_path, cell, colour):
    im = Image.open(img_path).convert("RGB")
    r, c = cell
    ImageDraw.Draw(im).rectangle([c * CELL, r * CELL, (c + 1) * CELL - 1, (r + 1) * CELL - 1], fill=colour)
    im.save(img_path)


def test_mutation_flipped_answer_key(small_set, tmp_path):
    root = _copy(small_set, tmp_path)
    caught = 0
    tasks = _load(root)
    for t in tasks:
        wrong = next(c for c in t["choices"] if c != t["answer"])
        caught += verify_task(root, {**t, "answer": wrong}) is not None
    assert caught == len(tasks)


def test_mutation_erased_doorway(small_set, tmp_path):
    root = _copy(small_set, tmp_path)
    caught = tried = 0
    for t in _load(root):
        g = np.array(t["scene"]["grid"])
        doors = np.argwhere(g == 2)
        if len(doors) == 0:
            continue
        _paint_cell(root / t["image"], tuple(doors[0]), STYLES[t["style"]][1])  # paint door as wall
        tried += 1
        caught += verify_task(root, t) is not None
    assert tried > 0 and caught == tried


def test_mutation_moved_goal(small_set, tmp_path):
    root = _copy(small_set, tmp_path)
    caught = tried = 0
    for t in _load(root):
        goals = t["scene"]["goals"]
        if "A" not in goals:
            continue
        r, c = goals["A"]
        _paint_cell(root / t["image"], (r, c), STYLES[t["style"]][0])  # erase goal A
        tried += 1
        caught += verify_task(root, t) is not None
    assert tried > 0 and caught == tried


def test_mutation_scene_label_swapped(small_set):
    caught = tried = 0
    for t in _load(small_set):
        goals = t["scene"]["goals"]
        if len(goals) < 2:
            continue
        g = dict(goals)
        g["A"], g["B"] = g["B"], g["A"]
        tried += 1
        caught += verify_task(small_set, {**t, "scene": {**t["scene"], "goals": g}}) is not None
    assert tried > 0 and caught == tried


def test_mutation_heading_flipped(small_set):
    flip = {"N": "S", "S": "N", "E": "W", "W": "E"}
    caught = 0
    tasks = _load(small_set)
    for t in tasks:
        sc = {**t["scene"], "heading": flip[t["scene"]["heading"]]}
        caught += verify_task(small_set, {**t, "scene": sc}) is not None
    assert caught == len(tasks)
