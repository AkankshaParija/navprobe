"""Procedural hospital-floor maps.

A map is a grid of cells. Every answer in NavProbe is computed from this grid
plus the robot and goal markers -- never from a model.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# Cell classes
FREE, WALL, DOOR, CLOSED, FURN = 0, 1, 2, 3, 4
CLASS_NAMES = {FREE: "floor", WALL: "wall", DOOR: "open_door", CLOSED: "closed_door", FURN: "furniture"}

# Headings as (d_row, d_col); north is up in the image.
HEADINGS = {"N": (-1, 0), "E": (0, 1), "S": (1, 0), "W": (0, -1)}
GOAL_LABELS = ("A", "B", "C")


@dataclass
class Scene:
    grid: np.ndarray                      # (H, W) int8 of cell classes
    robot: tuple[int, int]                # top-left cell of the robot footprint
    robot_size: int = 1                   # footprint is robot_size x robot_size cells
    heading: str = "N"
    goals: dict[str, tuple[int, int]] = field(default_factory=dict)

    def copy(self) -> "Scene":
        return Scene(self.grid.copy(), tuple(self.robot), self.robot_size, self.heading, dict(self.goals))

    def to_json(self) -> dict:
        return {
            "grid": self.grid.tolist(),
            "robot": list(self.robot),
            "robot_size": self.robot_size,
            "heading": self.heading,
            "goals": {k: list(v) for k, v in self.goals.items()},
        }


@dataclass
class MapParams:
    size: int = 28                 # grid is size x size
    min_room: int = 4              # minimum room interior width
    door_widths: tuple = (1, 2)
    extra_doors: int = 3           # extra doorways that create loops
    furniture_per_room: tuple = (0, 3)
    close_prob: float = 0.0        # probability that a doorway is drawn closed


# ---------------------------------------------------------------- generation

def _forbidden_lines(grid, r0, c0, r1, c1, axis):
    """Rows (axis=0) or cols (axis=1) where a new wall would touch an existing doorway."""
    bad = set()
    H, W = grid.shape
    if axis == 0:  # horizontal wall at some row -> check doors in the left/right boundary walls
        for r in range(r0, r1 + 1):
            for c in (c0 - 1, c1 + 1):
                if 0 <= c < W and grid[r, c] in (DOOR, CLOSED):
                    bad.update({r - 1, r, r + 1})
    else:
        for c in range(c0, c1 + 1):
            for r in (r0 - 1, r1 + 1):
                if 0 <= r < H and grid[r, c] in (DOOR, CLOSED):
                    bad.update({c - 1, c, c + 1})
    return bad


def _split(rng, grid, rect, p: MapParams, rooms):
    r0, c0, r1, c1 = rect
    h, w = r1 - r0 + 1, c1 - c0 + 1
    m = p.min_room
    options = []
    if h >= 2 * m + 1:
        rows = [r for r in range(r0 + m, r1 - m + 1) if r not in _forbidden_lines(grid, r0, c0, r1, c1, 0)]
        if rows:
            options.append(("h", rows))
    if w >= 2 * m + 1:
        cols = [c for c in range(c0 + m, c1 - m + 1) if c not in _forbidden_lines(grid, r0, c0, r1, c1, 1)]
        if cols:
            options.append(("v", cols))
    # Stop splitting at random once rooms are reasonably small, so room sizes vary.
    if not options or (max(h, w) < 3 * m and rng.random() < 0.35):
        rooms.append(rect)
        return
    if len(options) == 2:  # prefer cutting the longer side
        kind, lines = options[0] if h > w else options[1]
        if rng.random() < 0.25:
            kind, lines = options[int(rng.integers(2))]
    else:
        kind, lines = options[0]
    line = int(rng.choice(lines))
    dw = int(rng.choice(p.door_widths))
    if kind == "h":
        grid[line, c0:c1 + 1] = WALL
        start = int(rng.integers(c0, c1 - dw + 2))
        for c in range(start, start + dw):
            grid[line, c] = DOOR
        _split(rng, grid, (r0, c0, line - 1, c1), p, rooms)
        _split(rng, grid, (line + 1, c0, r1, c1), p, rooms)
    else:
        grid[r0:r1 + 1, line] = WALL
        start = int(rng.integers(r0, r1 - dw + 2))
        for r in range(start, start + dw):
            grid[r, line] = DOOR
        _split(rng, grid, (r0, c0, r1, line - 1), p, rooms)
        _split(rng, grid, (r0, line + 1, r1, c1), p, rooms)


def _room_of(rooms, r, c):
    for i, (r0, c0, r1, c1) in enumerate(rooms):
        if r0 <= r <= r1 and c0 <= c <= c1:
            return i
    return -1


def _add_extra_doors(rng, grid, rooms, p: MapParams):
    """Carve extra doorways between neighbouring rooms so maps contain loops."""
    H, W = grid.shape
    added = 0
    for _ in range(400):
        if added >= p.extra_doors:
            break
        r, c = int(rng.integers(1, H - 1)), int(rng.integers(1, W - 1))
        if grid[r, c] != WALL:
            continue
        # (offset to the two sides of the wall, direction along the wall)
        for side, along in (((0, 1), (1, 0)), ((1, 0), (0, 1))):
            dw = int(rng.choice(p.door_widths))
            cells = [(r + along[0] * k, c + along[1] * k) for k in range(dw)]
            pairs, ok = set(), True
            for (cr, cc) in cells:
                if not (1 <= cr < H - 1 and 1 <= cc < W - 1) or grid[cr, cc] != WALL:
                    ok = False
                    break
                a = _room_of(rooms, cr - side[0], cc - side[1])
                b = _room_of(rooms, cr + side[0], cc + side[1])
                if a < 0 or b < 0 or a == b:
                    ok = False
                    break
                pairs.add((a, b))
                if np.isin(grid[max(cr - 2, 0):cr + 3, max(cc - 2, 0):cc + 3], (DOOR, CLOSED)).any():
                    ok = False
                    break
            if ok and len(pairs) == 1:
                for (cr, cc) in cells:
                    grid[cr, cc] = DOOR
                added += 1
                break


def _add_furniture(rng, grid, rooms, p: MapParams):
    H, W = grid.shape
    near_door = np.zeros_like(grid, dtype=bool)
    for r, c in zip(*np.where(np.isin(grid, (DOOR, CLOSED)))):
        near_door[max(r - 2, 0):r + 3, max(c - 2, 0):c + 3] = True
    lo, hi = p.furniture_per_room
    for (r0, c0, r1, c1) in rooms:
        for _ in range(int(rng.integers(lo, hi + 1))):
            for _try in range(10):
                fh, fw = [(1, 2), (2, 1), (1, 1), (2, 2)][int(rng.integers(4))]
                r = int(rng.integers(r0, r1 - fh + 2))
                c = int(rng.integers(c0, c1 - fw + 2))
                block = grid[r:r + fh, c:c + fw]
                halo = grid[max(r - 1, 0):r + fh + 1, max(c - 1, 0):c + fw + 1]
                if block.shape != (fh, fw) or (block != FREE).any() or (halo == FURN).any():
                    continue
                if near_door[r:r + fh, c:c + fw].any():
                    continue
                grid[r:r + fh, c:c + fw] = FURN
                break


def generate_layout(rng: np.random.Generator, p: MapParams):
    """Return (grid, rooms). Rooms are interior rectangles (r0, c0, r1, c1)."""
    n = p.size
    grid = np.full((n, n), FREE, dtype=np.int8)
    grid[0, :] = grid[-1, :] = grid[:, 0] = grid[:, -1] = WALL
    rooms: list = []
    _split(rng, grid, (1, 1, n - 2, n - 2), p, rooms)
    _add_extra_doors(rng, grid, rooms, p)
    if p.close_prob > 0:
        close_doorways(rng, grid, p.close_prob)
    _add_furniture(rng, grid, rooms, p)
    return grid, rooms


def doorway_components(grid):
    """List of doorways, each a list of cells (4-connected door / closed-door cells)."""
    from scipy.ndimage import label
    lab, n = label(np.isin(grid, (DOOR, CLOSED)))
    return [list(zip(*np.where(lab == i))) for i in range(1, n + 1)]


def close_doorways(rng, grid, prob):
    for cells in doorway_components(grid):
        if rng.random() < prob:
            for (r, c) in cells:
                grid[r, c] = CLOSED


def free_cells(grid, size=1, avoid=()):
    """Top-left cells where a size x size block is entirely FREE and not within 1 cell of `avoid` blocks."""
    H, W = grid.shape
    ok = grid == FREE
    out = []
    for r in range(H - size + 1):
        for c in range(W - size + 1):
            if not ok[r:r + size, c:c + size].all():
                continue
            clash = False
            for (ar, ac, asz) in avoid:
                if r <= ar + asz and ar <= r + size and c <= ac + asz and ac <= c + size:
                    clash = True
                    break
            if not clash:
                out.append((r, c))
    return out


def place_markers(rng, grid, robot_size=1, n_goals=1):
    """Place the robot and goals on free cells, never touching each other. Returns Scene or None."""
    spots = free_cells(grid, robot_size)
    if not spots:
        return None
    robot = spots[int(rng.integers(len(spots)))]
    heading = str(rng.choice(list(HEADINGS)))
    taken = [(robot[0], robot[1], robot_size)]
    goals = {}
    for lab in GOAL_LABELS[:n_goals]:
        cands = free_cells(grid, 1, avoid=taken)
        if not cands:
            return None
        g = cands[int(rng.integers(len(cands)))]
        goals[lab] = g
        taken.append((g[0], g[1], 1))
    return Scene(grid, robot, robot_size, heading, goals)
