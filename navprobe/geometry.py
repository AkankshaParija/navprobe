"""Exact answer computation. Everything here works only on the grid + markers,
so the same functions can be run on a map decoded back from the PNG."""
from __future__ import annotations

import math
from collections import deque

import numpy as np
from scipy.ndimage import distance_transform_edt, label

from .mapgen import CLOSED, DOOR, FREE, FURN, HEADINGS, WALL

STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def passable(grid) -> np.ndarray:
    """Cells the robot can drive over: floor and open doorways."""
    return np.isin(grid, (FREE, DOOR))


def bfs(mask: np.ndarray, start) -> np.ndarray:
    """4-connected shortest-path lengths from `start` over True cells (-1 = unreachable)."""
    H, W = mask.shape
    dist = np.full((H, W), -1, dtype=np.int32)
    if not mask[start]:
        return dist
    dist[start] = 0
    q = deque([start])
    while q:
        r, c = q.popleft()
        for dr, dc in STEPS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and mask[nr, nc] and dist[nr, nc] < 0:
                dist[nr, nc] = dist[r, c] + 1
                q.append((nr, nc))
    return dist


def config_space(mask: np.ndarray, size: int) -> np.ndarray:
    """True at (r, c) if a size x size robot with top-left (r, c) fits entirely on True cells."""
    if size == 1:
        return mask.copy()
    H, W = mask.shape
    S = np.zeros((H + 1, W + 1), dtype=np.int32)
    S[1:, 1:] = mask.astype(np.int32).cumsum(0).cumsum(1)
    blk = S[size:, size:] - S[:-size, size:] - S[size:, :-size] + S[:-size, :-size]
    out = np.zeros_like(mask, dtype=bool)
    out[: H - size + 1, : W - size + 1] = blk == size * size
    return out


def can_reach(grid, robot, robot_size, goal) -> bool:
    """Can a robot_size x robot_size robot drive until its footprint covers `goal`?"""
    cs = config_space(passable(grid), robot_size)
    d = bfs(cs, tuple(robot))
    gr, gc = goal
    for r in range(gr - robot_size + 1, gr + 1):
        for c in range(gc - robot_size + 1, gc + 1):
            if 0 <= r < cs.shape[0] and 0 <= c < cs.shape[1] and d[r, c] >= 0:
                return True
    return False


def path_lengths(grid, robot, goals) -> dict:
    """Driving distance (cells) from a 1-cell robot to each goal; None if unreachable."""
    d = bfs(passable(grid), tuple(robot))
    return {k: (int(d[g]) if d[g] >= 0 else None) for k, g in goals.items()}


def center(cell, size=1):
    return (cell[0] + size / 2.0, cell[1] + size / 2.0)


def euclid(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def rooms_and_doors(grid):
    """Rooms = 4-connected regions of floor+furniture; doorways = 4-connected door cells.
    Returns (room_labels, doorway_list) where each doorway is (is_open, cells)."""
    room_lab, _ = label(np.isin(grid, (FREE, FURN)))
    door_lab, n = label(np.isin(grid, (DOOR, CLOSED)))
    doors = []
    for i in range(1, n + 1):
        cells = list(zip(*np.where(door_lab == i)))
        doors.append((bool(grid[cells[0]] == DOOR), cells))
    return room_lab, doors


def doors_of_room(grid, cell):
    """(open, closed) doorway counts touching the room that contains `cell`."""
    room_lab, doors = rooms_and_doors(grid)
    rid = room_lab[cell]
    H, W = grid.shape
    n_open = n_closed = 0
    for is_open, cells in doors:
        touch = any(
            0 <= r + dr < H and 0 <= c + dc < W and room_lab[r + dr, c + dc] == rid
            for (r, c) in cells for dr, dc in STEPS
        )
        if touch:
            if is_open:
                n_open += 1
            else:
                n_closed += 1
    return n_open, n_closed


def relative_side(robot, robot_size, heading, goal):
    """Return ('left'|'right', angle_deg) of goal relative to the robot's facing direction.
    angle is 0 when straight ahead, 180 when straight behind."""
    rc = center(robot, robot_size)
    gc = center(goal)
    vx, vy = gc[1] - rc[1], -(gc[0] - rc[0])          # image -> math coords (y up)
    hr, hc = HEADINGS[heading]
    hx, hy = hc, -hr
    cross = hx * vy - hy * vx
    dot = hx * vx + hy * vy
    ang = math.degrees(math.atan2(abs(cross), dot))
    return ("left" if cross > 0 else "right"), ang


def line_of_sight(grid, a_center, b_center, k: int = 10, margin: float = 0.3):
    """Camera view from a to b (continuous cell coords). Walls, closed doors and furniture block it.
    Returns 'visible', 'blocked', or None when it is too close to call (ray grazes a corner)."""
    blocker = np.isin(grid, (WALL, CLOSED, FURN))
    up = np.kron(blocker, np.ones((k, k), dtype=bool))
    out_dist = distance_transform_edt(~up) / k        # free point -> nearest blocker
    in_depth = distance_transform_edt(up) / k         # blocked point -> nearest free
    n = int(euclid(a_center, b_center) * k * 2) + 2
    min_clear, max_depth = math.inf, 0.0
    for t in np.linspace(0.0, 1.0, n):
        y = a_center[0] + t * (b_center[0] - a_center[0])
        x = a_center[1] + t * (b_center[1] - a_center[1])
        iy, ix = min(int(y * k), up.shape[0] - 1), min(int(x * k), up.shape[1] - 1)
        if up[iy, ix]:
            max_depth = max(max_depth, in_depth[iy, ix])
        else:
            min_clear = min(min_clear, out_dist[iy, ix])
    if max_depth >= margin:
        return "blocked"
    if max_depth == 0.0 and min_clear >= margin:
        return "visible"
    return None
