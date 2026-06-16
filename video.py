#!/usr/bin/env python3


from videocode import *
from videocode.template.input._inputs import *


SLOT = 4.0  # seconds per demo


def label(text: str, t: sec):
    return (
        Text(text, fontSize=0.38, fillColor=WHITE | 0.7)
        .position(0, 3.6)
        .opacity(0)
        .fadeIn(start=t, duration=0.3)
        .fadeOut(start=t + SLOT - 0.4, hide=True)
    )


def fadeOutAt(inp: Input, t: sec):
    return inp.fadeOut(start=t, hide=True)


# ── 1. Highlight ─────────────────────────────────────────────────────────────
t0 = 0 * SLOT

label("highlight()", t0)
r1 = Rectangle(width=3, height=1.5, fillColor=BLUE_C | WHITE).position(0, 0)
r1.highlight(start=t0 + 0.4, duration=2.5)
fadeOutAt(r1, t0 + SLOT - 0.5)


# ── 2. SurroundingRectangle ───────────────────────────────────────────────────
t1 = 1 * SLOT

label("SurroundingRectangle()", t1)
r2 = Circle(radius=1.2, fillColor=RED_A).position(0, 0).opacity(0).fadeIn(start=t1, duration=0.4)
sr = SurroundingRectangle(r2).opacity(0).fadeIn(start=t1 + 0.5, duration=0.4)
fadeOutAt(r2, t1 + SLOT - 0.5)
fadeOutAt(sr, t1 + SLOT - 0.5)


# ── 3. Underline ─────────────────────────────────────────────────────────────
t2 = 2 * SLOT

label("Underline()", t2)
r3 = Rectangle(width=3.5, height=0.6, fillColor=BLUE_C | WHITE, strokeColor=TRANSPARENT).position(0, 0).opacity(0).fadeIn(start=t2, duration=0.4)
ul = Underline(r3, color=YELLOW).opacity(0).fadeIn(start=t2 + 0.5, duration=0.4)
fadeOutAt(r3, t2 + SLOT - 0.5)
fadeOutAt(ul, t2 + SLOT - 0.5)


# ── 4. Cross ─────────────────────────────────────────────────────────────────
t3 = 3 * SLOT

label("Cross()", t3)
r4 = Rectangle(width=2.5, height=1.5, fillColor=GREEN_A | BLACK, strokeColor=TRANSPARENT).position(0, 0).opacity(0).fadeIn(start=t3, duration=0.4)
x4 = Cross(r4).opacity(0).fadeIn(start=t3 + 0.5, duration=0.4)
fadeOutAt(r4, t3 + SLOT - 0.5)
fadeOutAt(x4, t3 + SLOT - 0.5)


# ── 5. FocusOn ───────────────────────────────────────────────────────────────
t4 = 4 * SLOT

label("FocusOn()", t4)
FocusOn(0, 0, start=t4 + 0.3, duration=2.5)


# ── 6. DashedLine ────────────────────────────────────────────────────────────
t5 = 5 * SLOT

label("DashedLine()", t5)
dl = DashedLine(-5, 0, 5, 0).opacity(0).fadeIn(start=t5, duration=0.5)
fadeOutAt(dl, t5 + SLOT - 0.5)
