#!/usr/bin/env python3

"""
The card an example opens on: a title, what is about to happen, and the code.

Every example in this folder shows one thing, and a viewer who does not
already know what to look for sees a shape moving. So each one opens on a
written card — the feature's name, the two or three things to watch, and the
lines that would write it — and cuts from it into the demonstration.

    intro = card(
        "A1 · Composition",
        "deux formes qui se chevauchent",
        "…",
        code=["c = Composition(a, b)", "c.fadeIn(duration=1)"],
    )
    with shot() as demo:
        ...
    cut(intro, demo)

It is a shot like any other, so `cut` puts it away at the frame the demo opens.
"""

import re

from videocode import *

INK = rgba(238, 240, 246)
DIM = rgba(150, 156, 170)

# Le panneau de code : les mêmes rôles que dans l'éditeur, en plus sobre.
CODE_BG = rgba(21, 25, 33)
CODE_EDGE = rgba(52, 60, 76)
CODE_INK = rgba(214, 220, 232)
CODE_NOTE = rgba(118, 126, 144)
CODE_STR = rgba(150, 205, 150)
CODE_NUM = rgba(226, 172, 108)
CODE_KEY = rgba(198, 152, 226)
MONO = "Menlo"

_TOKENS = re.compile(
    r"(?P<note>#.*$)"
    r"|(?P<text>\"[^\"]*\"|'[^']*')"
    r"|(?P<key>\b(?:with|as|for|in|if|else|not|and|or|def|return|import|from|True|False|None)\b)"
    r"|(?P<call>\b[A-Za-z_]\w*(?=\())"
    r"|(?P<num>\b\d+(?:\.\d+)?\b)"
)


def _painted(line: str, accent: rgba) -> str:
    """One source line, cut into coloured runs — `colored()` escapes each one."""
    hues = {"note": CODE_NOTE, "text": CODE_STR, "key": CODE_KEY, "call": accent, "num": CODE_NUM}
    out, at = "", 0
    for hit in _TOKENS.finditer(line):
        if hit.start() > at:
            out += colored(CODE_INK) | line[at:hit.start()]
        out += colored(hues[str(hit.lastgroup)]) | hit.group()
        at = hit.end()
    return out + (colored(CODE_INK) | line[at:])


def card(
    title: str,
    *bullets: str,
    code: tuple[str, ...] | list[str] = (),
    seconds: sec = 3.4,
    accent: rgba = BLUE_C,
) -> shot:
    """
    Open a shot holding a title, a bulleted list and the code, and return it.

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

    if code:
        # Sous les puces, la moitié que personne ne peut deviner en regardant la
        # démonstration : ce qu'il faut écrire pour l'obtenir. La fonte est
        # calculée pour que la ligne la PLUS LONGUE tienne dans le panneau et
        # que le panneau tienne dans l'image — un exemple qui déborde du cadre
        # ne s'en aperçoit qu'au rendu, et personne ne rend une carte deux fois.
        panelLeft = left - size * 0.35
        panelWidth = WORLD_WIDTH - (panelLeft - -WORLD_WIDTH / 2) * 2
        panelTop = top - size * 2.1 - len(bullets) * size * 1.15 - size * 0.5
        floor = -WORLD_HEIGHT / 2 + WORLD_HEIGHT * 0.05

        longest = max(len(line) for line in code)
        mono = min(
            WORLD_HEIGHT / 30,
            panelWidth * 0.94 / (longest * 0.62),          # Menlo avance de ~0,62 em
            (panelTop - floor) / (len(code) * 1.75 + 2.2),
        )
        step = mono * 1.75
        pad = mono * 1.1
        panelHeight = (len(code) - 1) * step + mono + pad * 2

        panel = Rectangle(width=panelWidth, height=panelHeight, fillColor=CODE_BG, strokeColor=CODE_EDGE)
        panel.strokeWidth = mono / 14
        panel.position(panelLeft + panelWidth / 2, panelTop - panelHeight / 2).opacity(0)
        panel.fadeIn(start=0.3, duration=0.35)

        for i, line in enumerate(code):
            if not line.strip():
                continue
            written = MarkupText(markup=_painted(line, accent), fontSize=mono, fontFamily=MONO)
            written.align(x=0).position(panelLeft + pad, panelTop - pad - mono / 2 - i * step).opacity(0)
            written.fadeIn(start=0.5 + i * 0.1, duration=0.3)

    wait(seconds)
    held.__exit__()
    return held
