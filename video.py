#!/usr/bin/env python3


from videocode.template.input import *
from videocode.template.misc.chess.chessboard import ChessBoard
from videocode.template.misc.example.marius import *
from videocode import *

p = Plane()

# ─────────────────────────────────────────────────────────────────────────────
# LinearGradient — varies along a direction (0° = left→right, 90° = bottom→top).
# RadialGradient  — varies by distance from the shape's center outward.
# ConicGradient   — sweeps around the shape's center, like CSS conic-gradient.
# All accept bare colors (auto-spaced 0%…100%) or (color, percent) stop pins.
# ─────────────────────────────────────────────────────────────────────────────

# Row 1 — LinearGradient
rect_linear = Rectangle(
    width=4,
    height=1.8,
    fillColor=LinearGradient(RED_B, BLUE_B),
    strokeColor=TRANSPARENT,
).position(x=-5, y=3.3)

rect_linear_angled = Rectangle(
    width=4,
    height=1.8,
    fillColor=LinearGradient(GREEN, RED_A, angle=45),
    strokeColor=TRANSPARENT,
).position(x=0, y=3.3)

rect_linear_breakpoints = Rectangle(
    width=4,
    height=1.8,
    fillColor=LinearGradient(RED_B, (GREEN, 20), WHITE),
    strokeColor=TRANSPARENT,
).position(x=5, y=3.3)

# Row 2 — RadialGradient on rectangles
rect_radial = Rectangle(
    width=4,
    height=1.8,
    fillColor=RadialGradient(WHITE, BLUE_B),
    strokeColor=TRANSPARENT,
).position(x=-5, y=1.1)

rect_radial_multi = Rectangle(
    width=4,
    height=1.8,
    fillColor=RadialGradient(WHITE, (rgba(255, 200, 50), 40), BLUE_B),
    strokeColor=TRANSPARENT,
).position(x=0, y=1.1)

rect_radial_dark = Rectangle(
    width=4,
    height=1.8,
    fillColor=RadialGradient(rgba(60, 20, 80), (rgba(180, 80, 200), 50), BLACK),
    strokeColor=TRANSPARENT,
).position(x=5, y=1.1)

# Row 3 — RadialGradient on circles
circle_radial = Circle(
    radius=0.95,
    fillColor=RadialGradient(WHITE, BLUE_B),
    strokeColor=TRANSPARENT,
).position(x=-5, y=-1.1)

circle_radial_multi = Circle(
    radius=0.95,
    fillColor=RadialGradient(WHITE, (rgba(255, 200, 50), 40), rgba(180, 60, 0)),
    strokeColor=TRANSPARENT,
).position(x=0, y=-1.1)

circle_radial_glow = Circle(
    radius=0.95,
    fillColor=RadialGradient(WHITE, (rgba(100, 200, 255), 60), rgba(0, 30, 80)),
    strokeColor=TRANSPARENT,
).position(x=5, y=-1.1)

# Row 4 — ConicGradient
circle_conic = Circle(
    radius=0.95,
    fillColor=ConicGradient(RED, BLUE),
    strokeColor=TRANSPARENT,
).position(x=-5, y=-3.3)

circle_conic_wheel = Circle(
    radius=0.95,
    fillColor=ConicGradient(RED, (rgba(255, 200, 50), 33), GREEN, (BLUE_B, 66), RED),
    strokeColor=TRANSPARENT,
).position(x=0, y=-3.3)

rect_conic_angled = Rectangle(
    width=4,
    height=1.8,
    fillColor=ConicGradient(WHITE, (rgba(255, 200, 50), 50), BLACK, angle=90),
    strokeColor=TRANSPARENT,
).position(x=5, y=-3.3)


# ─────────────────────────────────────────────────────────────────────────────
# FUTURE API — mirror / shadow (council decision D4, not yet implemented)
#
# Whenever a shader is applied to `leader`, `follower` gets the same shader
# with identical timing. Pure Python — no C++ changes.
# ─────────────────────────────────────────────────────────────────────────────

# leader   = Rectangle(width=3, height=1).position(x=-3)
# follower = Rectangle(width=3, height=1).position(x= 3)
#
# follower.shadow(leader)           # follower now mirrors all shaders on leader
#
# leader.moveBy(x=1)                # follower also moves by x=1, same timing
# leader.fadeTo(0)                  # follower also fades, same timing
