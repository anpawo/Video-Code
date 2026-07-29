#!/usr/bin/env python3

"""
Assertion-based tests for `fillIn` and the `GroupEffect` scope it relies on.

The load-bearing fact: applied to a `Text`, `fillIn` must reach the TEXT, not
its letters. Only the Text slices a gradient per letter (`Text.fillColor`'s
`onSet`); handed a letter, the effect paints the whole gradient inside that
glyph's own box, and a 12-letter word gets 12 little wipes instead of one.
That failure renders as something plausible, so it needs an assertion, not eyes.
Run directly: `python3 test/fillin_test.py`
"""

import sys
from typing import cast

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import BLUE_C, LinearGradient, RED_B, Rectangle, Text, WHITE
from videocode.shader.ishader import Effect, GroupEffect
from videocode.template.effect.other.fillIn import fillIn
from videocode.template.effect.other.highlight import highlight

# ── scope declaration ───────────────────────────────────────────────────────
section("fillIn — declares its scope in the type")
check("returns a GroupEffect", isinstance(fillIn(RED_B), GroupEffect))
check("still callable, so a leaf Input is unaffected", callable(fillIn(RED_B)))
check("an ordinary effect stays a plain Effect", isinstance(highlight(), Effect) and not isinstance(highlight(), GroupEffect))

# ── the whole point: the Text slices, a letter cannot ───────────────────────
section("fillIn on a Text — one gradient across the word, not one per letter")
word = Text("ABC", fontSize=0.8)
word.apply(fillIn(LinearGradient(BLUE_C, RED_B), duration=0.3))
sliced = [cast(LinearGradient, letter.fillColor) for letter in word.inputs]

check("every letter ends on a gradient", all(isinstance(f, LinearGradient) for f in sliced))
check("the letters do NOT share one gradient — the Text sliced it", len({str(f) for f in sliced}) == 3)
# Sliced left to right: each letter picks up where the previous one stopped.
check("slice 0 ends where slice 1 begins", abs(sliced[0].stops[-1][0].r - sliced[1].stops[0][0].r) <= 8)
check("slice 1 ends where slice 2 begins", abs(sliced[1].stops[-1][0].r - sliced[2].stops[0][0].r) <= 8)
check("the word starts on the first colour", sliced[0].stops[0][0] == BLUE_C)
check("the word ends on the last colour", sliced[-1].stops[-1][0] == RED_B)

# ── the failure this guards against ────────────────────────────────────────
section("regression guard — per-member dispatch repeats the gradient")
naive = Text("ABC", fontSize=0.8)
for letter in naive.inputs:
    letter.fillColor = LinearGradient(BLUE_C, RED_B)
repeated = [cast(LinearGradient, letter.fillColor) for letter in naive.inputs]

check("writing to each letter gives them all the SAME gradient (the bug)", len({str(f) for f in repeated}) == 1)
check("...which is exactly what the sliced version avoids", str(repeated[0]) != str(sliced[0]))

# ── leaf inputs ────────────────────────────────────────────────────────────
section("fillIn on a plain shape — no members to split for")
box = Rectangle(width=4, height=2, fillColor=WHITE)
box.apply(fillIn(RED_B, duration=0.3))

check("it ends on the target colour", box.fillColor == RED_B)

summary()
