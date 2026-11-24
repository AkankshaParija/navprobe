"""Read a rendered PNG back into a Scene using only pixel colours.

This is deliberately independent of the generator: it never sees the grid,
only the image. If decode(render(scene)) != scene, the evidence for the answer
is not reliably present in the image and the task is rejected.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from .mapgen import CLOSED, DOOR, FREE, FURN, GOAL_LABELS, HEADINGS, WALL, Scene
from .render import CELL, MARKERS, STYLES

MARKER_FRAC = 0.15  # share of a cell's pixels that must be marker-coloured


def _palette(style):
    pal = STYLES[style]
    names, cols = [], []
    for k in (FREE, WALL, DOOR, CLOSED, FURN):
        names.append(k)
        cols.append(pal[k])
    if pal["gridline"]:
        names.append(FREE)
        cols.append(pal["gridline"])
    for m in ("robot", *GOAL_LABELS, "ink"):
        names.append(m)
        cols.append(MARKERS[m])
    return names, np.array(cols, dtype=np.int32)


def decode(img: Image.Image, style: str, cell: int = CELL) -> Scene:
    arr = np.asarray(img.convert("RGB"), dtype=np.int32)
    Hp, Wp, _ = arr.shape
    H, W = Hp // cell, Wp // cell
    names, cols = _palette(style)
    # nearest palette colour for every pixel (classify each distinct colour once)
    packed = (arr[:, :, 0] << 16) | (arr[:, :, 1] << 8) | arr[:, :, 2]
    uniq, inv = np.unique(packed, return_inverse=True)
    ucols = np.stack([(uniq >> 16) & 255, (uniq >> 8) & 255, uniq & 255], -1)
    ulab = ((ucols[:, None, :] - cols[None, :, :]) ** 2).sum(-1).argmin(-1)
    lab = ulab[inv].reshape(Hp, Wp)
    blocks = lab.reshape(H, cell, W, cell).transpose(0, 2, 1, 3).reshape(H, W, cell * cell)

    def frac(idx_list):
        return np.isin(blocks, idx_list).mean(-1)

    idx = {}
    for i, n in enumerate(names):
        idx.setdefault(n, []).append(i)

    grid = np.full((H, W), FREE, dtype=np.int8)
    cls_frac = np.stack([frac(idx[k]) for k in (FREE, WALL, DOOR, CLOSED, FURN)], -1)
    grid[:] = np.array([FREE, WALL, DOOR, CLOSED, FURN], dtype=np.int8)[cls_frac.argmax(-1)]

    goals = {}
    for g in GOAL_LABELS:
        f = frac(idx[g])
        cells = list(zip(*np.where(f >= MARKER_FRAC)))
        if len(cells) == 1:
            goals[g] = (int(cells[0][0]), int(cells[0][1]))
            grid[cells[0]] = FREE
        elif len(cells) > 1:
            raise ValueError(f"goal {g} spans {len(cells)} cells")

    rf = frac(idx["robot"])
    rcells = np.argwhere(rf >= MARKER_FRAC)
    if len(rcells) == 0:
        raise ValueError("robot not found")
    (r0, c0), (r1, c1) = rcells.min(0), rcells.max(0)
    size = int(r1 - r0 + 1)
    if size != c1 - c0 + 1:
        raise ValueError("robot footprint is not square")
    grid[r0:r1 + 1, c0:c1 + 1] = FREE

    # heading: the arrow tip is the ink pixel that reaches farthest from the robot centre
    y0, x0 = r0 * cell, c0 * cell
    sub = lab[y0:y0 + size * cell, x0:x0 + size * cell]
    ys, xs = np.where(np.isin(sub, idx["ink"]))
    if len(ys) == 0:
        raise ValueError("robot arrow not found")
    vy, vx = ys + 0.5 - size * cell / 2, xs + 0.5 - size * cell / 2
    heading = max(HEADINGS, key=lambda h: (HEADINGS[h][0] * vy + HEADINGS[h][1] * vx).max())

    return Scene(grid, (int(r0), int(c0)), size, heading, goals)


def same_scene(a: Scene, b: Scene) -> bool:
    return (
        a.grid.shape == b.grid.shape
        and bool((a.grid == b.grid).all())
        and tuple(a.robot) == tuple(b.robot)
        and a.robot_size == b.robot_size
        and a.heading == b.heading
        and {k: tuple(v) for k, v in a.goals.items()} == {k: tuple(v) for k, v in b.goals.items()}
    )
