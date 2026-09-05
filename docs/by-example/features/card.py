#!/usr/bin/env python3

"""
The card an example opens on: a title, and what is about to happen.

Every example in this folder shows one thing, and a viewer who does not
already know what to look for sees a shape moving. So each one opens on a
written card — the feature's name and the two or three things to watch — and
cuts from it into the demonstration.

    intro = card("A1 · Composition", "deux formes qui se chevauchent", "…")
    with shot() as demo:
        ...
    cut(intro, demo)

It is a shot like any other, so `cut` puts it away at the frame the demo opens.
"""

from videocode import *

INK = rgba(238, 240, 246)
DIM = rgba(150, 156, 170)


def card(title: str, *bullets: str, seconds: sec = 3.4, accent: rgba = BLUE_C) -> shot:
    """
    Open a shot holding a title and a bulleted list, and return it.

    The lines arrive one after another rather than all at once: a list that
    appears whole is read as a block and skipped, and the stagger is what makes
    someone read the second one.

    Everything is placed from the world's own edges (`WORLD_WIDTH` /
    `WORLD_HEIGHT`, which `setScreen` rebinds), so the card holds together at
    any size — including the three shapes `--for` renders.
    """
    held = shot()
    held.__enter__()

    left = -WORLD_WIDTH / 2 + WORLD_WIDTH * 0.06
    top = WORLD_HEIGHT / 2 - WORLD_HEIGHT * 0.16
    size = WORLD_HEIGHT / 14

    Text(text=title, fontSize=size, fillColor=INK).align(x=0).position(left, top).fadeIn(duration=0.4)

    # A rule under the title, drawn from nothing, in the accent.
    rule = Rectangle(width=0, height=size / 16, fillColor=accent, strokeColor=TRANSPARENT)
    rule.align(x=0).position(left, top - size * 0.9)
    rule.ease("width", WORLD_WIDTH * 0.22, start=0.15, duration=0.5)

    for i, line in enumerate(bullets):
        y = top - size * 2.1 - i * size * 1.15
        dot = Circle(radius=size / 9, fillColor=accent, strokeColor=TRANSPARENT)
        dot.position(left + size / 6, y).opacity(0)
        dot.fadeIn(start=0.4 + i * 0.28, duration=0.3)

        text = Text(text=line, fontSize=size * 0.52, fillColor=DIM)
        text.align(x=0).position(left + size * 0.6, y).opacity(0)
        text.fadeIn(start=0.45 + i * 0.28, duration=0.35)

    wait(seconds)
    held.__exit__()
    return held
