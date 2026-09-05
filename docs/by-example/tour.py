#!/usr/bin/env python3

"""
Everything that landed on 5 September 2026, in one scene you can run.

Render it:      ./video-code --file docs/by-example/tour.py --generate tour.mp4
Look at one moment:  ./video-code --file docs/by-example/tour.py --generate tour.png --from 4
Four at once:        ./video-code --file docs/by-example/tour.py --generate tour.png --sheet 4 --from 0 --to 12
Every shape:         ./video-code --file docs/by-example/tour.py --generate tour.mp4 --for youtube,tiktok,square
Open it:             ./video-code --file docs/by-example/tour.py --editor

Rendering it exercises: shots and cuts, the camera and `pinToFrame`, a comp,
`moveAlong`, `BarChart`, and the chapters a render writes from `timestamp()` —
which it prints at the end, in the form a description box takes.

Opening it exercises the editor's half: the markers on the ruler (⇧← / ⇧→ jump
between them), the caret lighting the bar its line makes (⌘⏎ plays from there),
the easing curve on each effect row, and File → Export Video… (⌘E).
"""

from videocode import *
from videocode.input.interface.Comp import Comp
from videocode.template.input.BarChart import Leaderboard

TITLE = 0.9
LABEL = 0.3

# What the camera must not touch: a caption sits in the FRAME, not in the world,
# so it neither zooms nor pans with the picture.
caption = Text(text="videocode — 5 sept.", fontSize=LABEL, fillColor=WHITE)
caption.position(-4.6, -3.9)
caption.pinToFrame()


# ── 1. A title, and the shot it belongs to ───────────────────────────────────
timestamp("the opening")

with shot() as opening:
    title = Text(text="one scene, every feature", fontSize=TITLE, fillColor=WHITE)
    title.position(0, 0.4)
    title.fadeIn(duration=0.6)

    under = Text(text="written as code, rendered by the engine", fontSize=LABEL, fillColor=BLUE_C)
    under.position(0, -0.6)
    # Hidden first, because a fade that STARTS LATER claims nothing before it
    # starts — and what nothing claims is what the element already was, which
    # for a new element is fully opaque.
    under.opacity(0)
    under.fadeIn(start=0.3, duration=0.6)
    wait(3)


# ── 2. A comp: two shapes that fade as ONE ───────────────────────────────────
timestamp("a comp fades as one")

with shot() as badge:
    pair = Comp(
        Circle(radius=1.1, fillColor=WHITE, strokeColor=TRANSPARENT),
        Square(side=1.6, fillColor=WHITE, strokeColor=TRANSPARENT).position(1.2, 0),
    )
    pair.position(-3.2, 0)
    # Half opacity on the COMP, so the join reads flat instead of doubling up.
    pair.opacity(128)

    told = Text(text="one layer, one fade", fontSize=LABEL, fillColor=WHITE)
    told.position(2.8, 0)
    told.fadeIn(duration=0.5)
    wait(3)

cut(opening, badge)


# ── 3. A path walked at one speed, turned the way it goes ────────────────────
timestamp("along a path")

with shot() as travelling:
    road = Curve(
        [(-6, -1.6), (-3, 1.6), (0, -1.6), (3, 1.6), (6, -1.6)],
        strokeColor=rgba(120, 120, 140),
    )
    runner = RightTriangle(width=0.7, height=0.5, fillColor=BLUE_C, strokeColor=WHITE)
    runner.moveAlong(road, duration=2.4, face=True)
    wait(3)

cut(badge, travelling)


# ── 4. Data, with the number riding its bar ──────────────────────────────────
timestamp("the numbers")

with shot() as figures:
    board = Leaderboard(
        {"Ada": 12, "Grace": 31, "Alan": 22, "Katherine": 27},
        height=3.2,
        color=GREEN_A,
    )
    board.position(0, -0.2)
    board.grow(duration=1.0)
    wait(3)

cut(travelling, figures)


# ── 5. And the camera moves over all of it ───────────────────────────────────
timestamp("the camera")

camera.over(duration=1.5).zoom = 1.6
camera.moveTo(x=1.5, y=0.4, duration=1.5)
wait(2)
camera.over(duration=1.0).zoom = 1
camera.moveTo(x=0, y=0, duration=1.0)
wait(1.5)
