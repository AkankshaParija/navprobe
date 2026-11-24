"""Draw a Scene as a PNG in one of two map styles."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from .mapgen import CLOSED, DOOR, FREE, FURN, HEADINGS, WALL, Scene

CELL = 24  # pixels per grid cell

# Marker colours are shared across styles; map colours differ.
MARKERS = {
    "robot": (25, 95, 225),
    "A": (200, 0, 200),
    "B": (0, 150, 150),
    "C": (120, 70, 20),
    "ink": (255, 255, 255),  # letters on goals, arrow on robot
}

STYLES = {
    # Architectural floor-plan look: warm floor, faint grid, amber doorways.
    "plan": {
        FREE: (248, 245, 235), WALL: (45, 45, 62), DOOR: (245, 175, 35),
        CLOSED: (205, 35, 35), FURN: (140, 165, 200), "gridline": (226, 222, 208),
    },
    # ROS occupancy-grid look: white free space, black occupied, no grid.
    "ros": {
        FREE: (242, 242, 242), WALL: (0, 0, 0), DOOR: (120, 205, 120),
        CLOSED: (235, 70, 70), FURN: (115, 115, 115), "gridline": None,
    },
}

LEGEND = {
    "plan": ("dark navy = wall, cream = floor, amber = open doorway, red = closed door (impassable), "
             "light blue blocks = furniture (impassable)"),
    "ros": ("black = wall, white = floor, green = open doorway, red = closed door (impassable), "
            "grey blocks = furniture (impassable)"),
}
MARKER_LEGEND = ("The blue square is the robot; the white arrow on it shows the direction it is facing. "
                 "Coloured circles with letters are goals. One grid cell is the unit of distance.")


def _font(size):
    return ImageFont.load_default(size=size)


def render(scene: Scene, style: str = "plan", cell: int = CELL) -> Image.Image:
    pal = STYLES[style]
    H, W = scene.grid.shape
    img = Image.new("RGB", (W * cell, H * cell), pal[FREE])
    d = ImageDraw.Draw(img)
    if pal["gridline"]:
        for i in range(W + 1):
            d.line([(i * cell, 0), (i * cell, H * cell)], fill=pal["gridline"], width=1)
        for i in range(H + 1):
            d.line([(0, i * cell), (W * cell, i * cell)], fill=pal["gridline"], width=1)
    for r in range(H):
        for c in range(W):
            k = int(scene.grid[r, c])
            if k == FREE:
                continue
            x0, y0 = c * cell, r * cell
            inset = 2 if k == FURN else 0
            d.rectangle([x0 + inset, y0 + inset, x0 + cell - 1 - inset, y0 + cell - 1 - inset], fill=pal[k])

    # Goals
    font = _font(int(cell * 0.62))
    for lab, (r, c) in scene.goals.items():
        cx, cy = c * cell + cell / 2, r * cell + cell / 2
        rad = cell * 0.44
        d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=MARKERS[lab])
        d.text((cx, cy), lab, fill=MARKERS["ink"], font=font, anchor="mm")

    # Robot footprint + heading arrow
    s = scene.robot_size * cell
    r, c = scene.robot
    x0, y0 = c * cell, r * cell
    d.rounded_rectangle([x0 + 2, y0 + 2, x0 + s - 3, y0 + s - 3], radius=max(3, s // 6), fill=MARKERS["robot"])
    cx, cy = x0 + s / 2, y0 + s / 2
    dr, dc = HEADINGS[scene.heading]
    tip = (cx + dc * 0.38 * s, cy + dr * 0.38 * s)
    base = (cx - dc * 0.18 * s, cy - dr * 0.18 * s)
    half = 0.20 * s
    p1 = (base[0] + dr * half, base[1] - dc * half)
    p2 = (base[0] - dr * half, base[1] + dc * half)
    d.polygon([tip, p1, p2], fill=MARKERS["ink"])
    return img
