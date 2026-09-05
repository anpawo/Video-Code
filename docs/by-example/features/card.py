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

TITLE = 0.62
BULLET = 0.32
INK = rgba(238, 240, 246)
DIM = rgba(150, 156, 170)


def card(title: str, *bullets: str, seconds: sec = 3.4, accent: rgba = BLUE_C) -> shot:
    """
    Open a shot holding a title and a bulleted list, and return it.

    The lines arrive one after another rather than all at once: a list that
    appears whole is read as a block and skipped, and the stagger is what makes
    someone read the second line.
    """
    held = shot()
    held.__enter__()

    Text(text=title, fontSize=TITLE, fillColor=INK).position(-6.4, 2.6).align(x=0).fadeIn(duration=0.4)

    # A rule under the title, drawn from nothing, in the accent.
    rule = Rectangle(width=0, height=0.035, fillColor=accent, strokeColor=TRANSPARENT)
    rule.align(x=0).position(-6.4, 2.1)
    rule.ease("width", 3.2, start=0.15, duration=0.5)

    for i, line in enumerate(bullets):
        y = 1.2 - i * 0.62
        dot = Circle(radius=0.06, fillColor=accent, strokeColor=TRANSPARENT)
        dot.position(-6.25, y).opacity(0)
        dot.fadeIn(start=0.4 + i * 0.28, duration=0.3)

        text = Text(text=line, fontSize=BULLET, fillColor=DIM)
        text.align(x=0).position(-5.9, y).opacity(0)
        text.fadeIn(start=0.45 + i * 0.28, duration=0.35)

    wait(seconds)
    held.__exit__()
    return held
