"""The six question families.

Each family has:
  sample(rng, size)  -> Scene (random map + markers for this family)
  answer(scene)      -> (answer, evidence) or (None, reason) when the task would be ambiguous
  question           -> the question text
  choices            -> allowed answers (used for balancing, parsing and the random baseline)
  pair(scene)        -> optional minimal-pair partner Scene with the opposite answer

answer() uses only the grid + markers, so it can be re-run on the decoded PNG.
"""
from __future__ import annotations

import numpy as np

from .geometry import (can_reach, center, doors_of_room, euclid, line_of_sight, passable, bfs,
                       path_lengths, relative_side, rooms_and_doors)
from .mapgen import CLOSED, DOOR, MapParams, Scene, generate_layout, place_markers

FLIP = {"N": "S", "S": "N", "E": "W", "W": "E"}


class Family:
    name = ""
    choices: tuple = ()
    answer_format = ""

    def sample(self, rng, size) -> Scene | None:
        raise NotImplementedError

    def answer(self, scene: Scene):
        raise NotImplementedError

    def question(self, scene: Scene) -> str:
        raise NotImplementedError

    def pair(self, scene: Scene, rng):
        return None


def _layout(rng, size, **kw):
    grid, _ = generate_layout(rng, MapParams(size=size, **kw))
    return grid


def _different_rooms(scene, a, b):
    lab, _ = rooms_and_doors(scene.grid)
    return lab[a] != lab[b]


class CountDoors(Family):
    name = "F1_count_doors"
    choices = ("1", "2", "3", "4")
    answer_format = "integer"

    def sample(self, rng, size):
        return place_markers(rng, _layout(rng, size, close_prob=0.3, extra_doors=5), 1, 0)

    def answer(self, s):
        n_open, n_closed = doors_of_room(s.grid, tuple(s.robot))
        if n_open == 0 or n_open > 4:
            return None, "count_out_of_range"
        return str(n_open), {"open_doorways": n_open, "closed_doorways": n_closed}

    def question(self, s):
        return ("How many OPEN doorways lead out of the room the robot is in? "
                "Closed doors do not count; a doorway wider than one cell still counts as one doorway.")


class Direction(Family):
    name = "F2_direction"
    choices = ("left", "right")
    answer_format = "left/right"

    def sample(self, rng, size):
        return place_markers(rng, _layout(rng, size, close_prob=0.1), 1, 1)

    def answer(self, s):
        side, ang = relative_side(s.robot, s.robot_size, s.heading, s.goals["A"])
        if not 30 <= ang <= 150:
            return None, "direction_near_ahead_or_behind"
        return side, {"angle_from_heading_deg": round(ang, 1)}

    def question(self, s):
        return ("From the robot's own point of view (the direction its arrow points), "
                "is goal A on its left or on its right?")

    def pair(self, s, rng):
        t = s.copy()
        t.heading = FLIP[s.heading]
        return t


class Reachability(Family):
    name = "F3_reachability"
    choices = ("yes", "no")
    answer_format = "yes/no"

    def sample(self, rng, size):
        return place_markers(rng, _layout(rng, size, close_prob=0.35, extra_doors=2), 1, 1)

    def answer(self, s):
        if not _different_rooms(s, tuple(s.robot), s.goals["A"]):
            return None, "goal_in_same_room"
        ok = can_reach(s.grid, s.robot, 1, s.goals["A"])
        return ("yes" if ok else "no"), {"reachable": ok}

    def question(self, s):
        return ("The robot can only drive through open doorways; closed doors and furniture block it. "
                "Can the robot drive to goal A?")

    def pair(self, s, rng):
        """Close one open doorway so that goal A becomes unreachable (only if the answer was yes)."""
        if not can_reach(s.grid, s.robot, 1, s.goals["A"]):
            return None
        _, doors = rooms_and_doors(s.grid)
        order = rng.permutation(len(doors))
        for i in order:
            is_open, cells = doors[i]
            if not is_open:
                continue
            t = s.copy()
            for c in cells:
                t.grid[c] = CLOSED
            if not can_reach(t.grid, t.robot, 1, t.goals["A"]):
                return t
        return None


class Fit(Family):
    name = "F4_fit"
    choices = ("yes", "no")
    answer_format = "yes/no"

    def sample(self, rng, size):
        g = _layout(rng, size, door_widths=(1, 3), close_prob=0.1, extra_doors=2,
                    furniture_per_room=(0, 0), min_room=4)
        return place_markers(rng, g, 2, 1)

    def answer(self, s):
        if not _different_rooms(s, tuple(s.robot), s.goals["A"]):
            return None, "goal_in_same_room"
        if not can_reach(s.grid, s.robot, 1, s.goals["A"]):
            return None, "unreachable_even_for_point_robot"
        ok = can_reach(s.grid, s.robot, s.robot_size, s.goals["A"])
        return ("yes" if ok else "no"), {"fits": ok, "robot_size_cells": s.robot_size}

    def question(self, s):
        return (f"The robot is drawn to scale: it is {s.robot_size} x {s.robot_size} grid cells and its whole body "
                "must pass through every opening. Doorways are 1 or 3 cells wide. "
                "Can the robot drive until it is on top of goal A?")

    def pair(self, s, rng):
        """Same map, 1-cell robot: always fits, so a 'no' task gets a 'yes' partner."""
        if s.robot_size == 1:
            return None
        t = s.copy()
        t.robot_size = 1
        return t


class Nearest(Family):
    name = "F5_nearest_by_path"
    choices = ("A", "B", "C")
    answer_format = "A/B/C"

    def sample(self, rng, size):
        return place_markers(rng, _layout(rng, size, close_prob=0.15, extra_doors=2), 1, 3)

    def answer(self, s):
        pl = path_lengths(s.grid, s.robot, s.goals)
        if any(v is None for v in pl.values()):
            return None, "goal_unreachable"
        order = sorted(pl, key=pl.get)
        best, second = pl[order[0]], pl[order[1]]
        if second < best * 1.2 or second - best < 3:
            return None, "path_lengths_too_close"
        rc = center(s.robot, s.robot_size)
        eu = {k: euclid(rc, center(g)) for k, g in s.goals.items()}
        e_order = sorted(eu, key=eu.get)
        return order[0], {"path_len": pl, "euclid": {k: round(v, 2) for k, v in eu.items()},
                          "straight_line_nearest": e_order[0], "trap": e_order[0] != order[0]}

    def question(self, s):
        return ("The robot drives along the floor (it cannot pass walls, closed doors or furniture). "
                "Which goal is closest to the robot by DRIVING distance, not straight-line distance?")


class LineOfSight(Family):
    name = "F6_line_of_sight"
    choices = ("visible", "blocked")
    answer_format = "visible/blocked"

    def sample(self, rng, size):
        return place_markers(rng, _layout(rng, size, close_prob=0.2, extra_doors=3), 1, 1)

    def answer(self, s):
        a = center(s.robot, s.robot_size)
        b = center(s.goals["A"])
        if euclid(a, b) < 5:
            return None, "too_close"
        v = line_of_sight(s.grid, a, b)
        if v is None:
            return None, "sight_line_grazes_obstacle"
        return v, {"distance_cells": round(euclid(a, b), 2)}

    def question(self, s):
        return ("Imagine a straight line from the centre of the robot to the centre of goal A. "
                "Walls, closed doors and furniture block the view; open doorways and floor do not. "
                "Ignore which way the robot faces. Is goal A visible or blocked?")


FAMILIES = [CountDoors(), Direction(), Reachability(), Fit(), Nearest(), LineOfSight()]
BY_NAME = {f.name: f for f in FAMILIES}
