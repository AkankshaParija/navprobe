import numpy as np

from navprobe.geometry import (bfs, can_reach, config_space, doors_of_room, line_of_sight, passable,
                               relative_side)
from navprobe.mapgen import CLOSED, DOOR, FREE, WALL


def parse(rows):
    m = {".": FREE, "#": WALL, "d": DOOR, "x": CLOSED}
    return np.array([[m[ch] for ch in r] for r in rows], dtype=np.int8)


TWO_ROOMS = parse([
    "#########",
    "#...#...#",
    "#...d...#",
    "#...#...#",
    "#########",
])


def test_bfs_through_door():
    d = bfs(passable(TWO_ROOMS), (1, 1))
    assert d[1, 7] == 8  # (1,1)->(2,1)->...->(2,4 door)->...->(1,7)


def test_closed_door_blocks():
    g = TWO_ROOMS.copy()
    g[2, 4] = CLOSED
    assert bfs(passable(g), (1, 1))[1, 7] == -1
    assert not can_reach(g, (1, 1), 1, (1, 7))


def test_footprint_cannot_pass_narrow_door():
    assert can_reach(TWO_ROOMS, (1, 1), 1, (2, 6))
    assert not can_reach(TWO_ROOMS, (1, 1), 2, (2, 6))  # 1-cell door, 2-cell robot


def test_config_space():
    cs = config_space(passable(TWO_ROOMS), 2)
    assert cs[1, 1] and cs[2, 2] and not cs[1, 3]


def test_doors_of_room():
    g = parse([
        "#########",
        "#...#...#",
        "#...d...#",
        "##x##...#",
        "#...#...#",
        "#########",
    ])
    assert doors_of_room(g, (1, 1)) == (1, 1)
    assert doors_of_room(g, (1, 6)) == (1, 0)


def test_relative_side():
    # robot at (5,5) facing north; goal to the east is on the right
    assert relative_side((5, 5), 1, "N", (5, 9))[0] == "right"
    assert relative_side((5, 5), 1, "N", (5, 1))[0] == "left"
    assert relative_side((5, 5), 1, "S", (5, 9))[0] == "left"
    assert relative_side((5, 5), 1, "E", (1, 5))[0] == "left"
    assert relative_side((5, 5), 1, "E", (1, 5))[1] == 90.0


def test_line_of_sight():
    assert line_of_sight(TWO_ROOMS, (1.5, 1.5), (1.5, 7.5)) == "blocked"
    assert line_of_sight(TWO_ROOMS, (2.5, 1.5), (2.5, 7.5)) == "visible"
    # grazing the wall corner next to the door is too close to call
    assert line_of_sight(TWO_ROOMS, (2.5, 1.5), (1.9, 7.5)) is None
