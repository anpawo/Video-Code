#!/usr/bin/env python3


from videocode.template.input import *
from videocode.template.misc.example.marius import *
from videocode import *

# --- Marius' Test (Do not remove, just comment it, you should try it also)
# p = SoftPlane()
example0()


# ─────────────────────────────────────────────────────────────────────────────
# CURRENT API — solid colors (works today)
# ─────────────────────────────────────────────────────────────────────────────

# rect = Rectangle(
#     width=4,
#     height=2,
#     fillColor=RED_B,  # rgba — solid color
#     strokeColor=WHITE,
#     strokeWidth=0.05,
# )

# text = Text(
#     "Hello World",
#     fillColor=BLUE_B,  # rgba — solid color
#     strokeColor=WHITE,
#     strokeWidth=0.03,
#     fontSize=0.75,
# ).position(y=-2)


# ─────────────────────────────────────────────────────────────────────────────
# FUTURE API — gradient colors (council decision D6, not yet implemented)
#
# `Gradient(*stops, angle)` is a new type accepted anywhere rgba is accepted.
# fillColor / strokeColor will be typed as `rgba | Gradient` (a `paint` union).
# Rendering happens in the fragment shader — no new earcut/geometry work.
# ─────────────────────────────────────────────────────────────────────────────

# rect_gradient = Rectangle(
#     width=4, height=2,
#     fillColor=Gradient(           # linear gradient, left→right (angle=0)
#         (0.0, RED_B),             # stop at 0%: RED_B
#         (1.0, BLUE_B),            # stop at 100%: BLUE_B
#         angle=0,                  # 0° = horizontal left→right
#     ),
#     strokeColor=WHITE,
#     strokeWidth=0.05,
# )

# text_gradient = Text(
#     "Hello World",
#     fillColor=Gradient(
#         (0.0, YELLOW),
#         (0.5, RED_B),
#         (1.0, PURPLE),
#         angle=90,                 # 90° = vertical top→bottom
#     ),
#     fontSize=0.75,
# ).position(y=-2)

# # Possible sugar shorthand (one-liner two-stop gradient):
# # rect2 = Rectangle(fillColor=RED_B.to(BLUE_B))    # if we add .to() later


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
