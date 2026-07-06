#!/usr/bin/env python3

"""
Assertion-based tests for adjustment layers (Tier 2).

An `AdjustmentLayer()` is an invisible, full-frame `Input` whose applied
fragment effects grade the flattened composite of everything below its zIndex.
No GPU here — this only checks the stack shape the renderer keys off:
  1. `AdjustmentLayer()` auto-applies the `adjustmentLayer` VertexShader, which
     sets `meta.isAdjustmentLayer`.
  2. `.apply(effect)` on it is the ordinary Input mechanism — the effect lands in
     the same stack slot / shape as on any other Input (no new API surface).
  3. Re-marking is idempotent (autodestroy).
Run directly: `python3 test/adjustment_layer_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *


def framesWith(index: int, key: str) -> dict[int, dict]:
    return {f: entry[key] for f, entry in Context.stack[index].items() if f != -1 and key in entry}


# ---------------------------------------------------------------------------
section("adjustment layer — marker lands in the stack, sets the flag")

al = AdjustmentLayer().zIndex(5)

check("meta.isAdjustmentLayer is True", al.meta.isAdjustmentLayer is True)
check("zIndex reflects the anchor", al.meta.zIndex == 5)

marker = framesWith(al.meta.index, "AdjustmentLayer")
check("AdjustmentLayer entry present", len(marker) == 1)
entry = next(iter(marker.values()))
check("shaderType is VertexShader", entry["type"] == "VertexShader")

# ---------------------------------------------------------------------------
section("adjustment layer — .apply(effect) uses the ordinary Input mechanism")

al.apply(grayscale(), duration=1)
effs = framesWith(al.meta.index, "Grayscale")
check("Grayscale FragmentShader lands like on any Input", len(effs) > 0)
check("shaderType is FragmentShader", next(iter(effs.values()))["type"] == "FragmentShader")
# Marking as an adjustment layer does not disturb the effect stack.
check("still flagged after applying an effect", al.meta.isAdjustmentLayer is True)

# ---------------------------------------------------------------------------
section("adjustment layer — re-marking is idempotent (autodestroy)")

from videocode.shader.vertexShader.adjustmentLayer import adjustmentLayer

al2 = AdjustmentLayer()
al2.apply(adjustmentLayer())  # second mark — should autodestroy, single entry
again = framesWith(al2.meta.index, "AdjustmentLayer")
check("re-marking does not stack twice", len(again) == 1)

# ---------------------------------------------------------------------------
section("adjustment layer — a plain Input is NOT an adjustment layer")

r = Rectangle(width=2, height=2)
check("plain Input flag defaults False", r.meta.isAdjustmentLayer is False)

# ---------------------------------------------------------------------------
summary()
