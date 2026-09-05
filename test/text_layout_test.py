#!/usr/bin/env python3

"""
A word is only a word if its letters are told where they go.

`Text` lays its letters out at construction and writes that layout into each
letter's `meta.position`, then emits it as a position claim. The emission was
being thrown away: a position shader that matches the meta it would write is
dropped as a write with no effect, and the meta had just been set to the same
value. Python knew the layout, the renderer never heard it, and C++ starts
every input at the origin — so a text nobody moved drew its letters on one
spot.

Nothing in the corpus caught it, because every scene in it places its text
somewhere other than the exact centre.

Run directly: `python3 test/text_layout_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Text
from videocode.context import Context
from videocode.serialize import _resetContext


def letterXs(text: Text) -> list[float]:
    """Where each letter is CLAIMED to be — what the renderer is told."""
    out = []
    for letter in text.inputs:
        entry = Context.stack.get(letter.meta.index, {})
        claimed = [shader["args"]["x"]
                   for frame, keys in entry.items() if frame != -1
                   for key, shader in keys.items()
                   if key.startswith("Position") and shader["args"].get("x") is not None]
        out.append(claimed[0] if claimed else None)
    return out


section("a text nobody moved still says where its letters are")
_resetContext()
plain = Text(text="Kate", fontSize=0.28)
xs = letterXs(plain)
check(f"every letter is claimed somewhere ({xs})", all(x is not None for x in xs))
check("and no two of them at the same place", len(set(xs)) == len(xs))
check("in reading order, left to right", xs == sorted(xs))

section("the same word placed at the origin — the case that used to collapse")
_resetContext()
centred = Text(text="Kate", fontSize=0.28).position(0, 0)
check("its letters are claimed too", all(x is not None for x in letterXs(centred)))

section("and placed anywhere else, as it always did")
_resetContext()
moved = Text(text="Kate", fontSize=0.28).position(1, 0)
check("shifted by exactly where it was put",
      all(abs((there or 0) - here - 1) < 1e-6 for here, there in zip(xs, letterXs(moved))))

section("the letters know it too, not only the stack")
_resetContext()
metas = [round(letter.meta.position.x, 3) for letter in Text(text="Kate", fontSize=0.28).inputs]
check(f"their own positions hold the layout ({metas})", len(set(metas)) == len(metas))

# ── The reader that has no stack ───────────────────────────────────────────
# `CompoundPolygon(*Text(...).inputs)` unions the letters' outlines and reads
# their layout straight off `meta` — inside `noRegister`, where nothing reaches
# the stack at all. The matte and silk scenes do exactly this, and zeroing the
# meta for them collapses the word onto one spot.
section("a text built to be read, not drawn, keeps its layout in meta")
_resetContext()
with Context.noRegister():
    unregistered = Text(text="MATTE", fontSize=2.4).inputs
spread = [round(letter.meta.position.x, 2) for letter in unregistered]
check(f"five letters, five places ({spread})", len(set(spread)) == len(spread))

summary()
