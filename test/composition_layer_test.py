#!/usr/bin/env python3

"""
Assertion-based tests for compositions (a group that renders as ONE layer).

A `Composition` is a `Group` that also owns an invisible full-frame layer: its members
are flattened into that layer, and the layer is what carries the composition's
opacity, effects and matte. No GPU here — this checks the stack shape the
renderers key off:
  1. the layer is marked (`composition` VertexShader → `meta.isComposition`) and every member
     points back at it (`compositionMember` → `meta.compositionIndex`);
  2. a compositing claim lands on the LAYER and nowhere else — that is what
     makes a group fade one flat fade instead of one per member;
  3. a rigid transform still reaches the members, as in any `Group`;
  4. a `Composition` answers with its layer's index, so `matte(composition)` is one input.
Run directly: `python3 test/composition_layer_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.shader.vertexShader.composition import composition
from videocode.shader.vertexShader.compositionMember import compositionMember


def keysOf(index: int) -> list[str]:
    """Every shader name written into an input's stack slot, frames only."""
    return [k for f, entry in Context.stack[index].items() if f != -1 for k in entry]


# ---------------------------------------------------------------------------
section("composition — the layer is marked and the members point at it")

a = Square(side=2, fillColor=WHITE)
b = Square(side=2, fillColor=WHITE).position(1, 0)
c = Composition(a, b)

check("layer is flagged isComposition", c.layer.meta.isComposition is True)
check("layer got a slot of its own", c.layer.meta.index is not None)
check("Composition marker in the layer's stack", keysOf(c.layer.meta.index).count("Composition") == 1)
check("member a points at the layer", a.meta.compositionIndex == c.layer.meta.index)
check("member b points at the layer", b.meta.compositionIndex == c.layer.meta.index)
check("CompositionMember written once per member", keysOf(a.meta.index).count("CompositionMember") == 1)
check("a plain Input is not a member", Square(side=1).meta.compositionIndex is None)

# ---------------------------------------------------------------------------
section("composition — a compositing claim lands on the LAYER, not on the members")

c.opacity(128)
check("Opacity on the layer", "Opacity" in keysOf(c.layer.meta.index))
check("no Opacity on member a", "Opacity" not in keysOf(a.meta.index))
check("no Opacity on member b", "Opacity" not in keysOf(b.meta.index))
check("the group's own meta stays truthful", c.meta.opacity == 128)

c.apply(grayscale(), duration=1)
check("fragment effect on the layer", "Grayscale" in keysOf(c.layer.meta.index))
check("no effect on member a", "Grayscale" not in keysOf(a.meta.index))

c.zIndex(7)
check("zIndex on the layer", c.layer.meta.zIndex == 7)
check("member zIndex untouched", a.meta.zIndex != 7)

# ---------------------------------------------------------------------------
section("composition — rigid transforms still reach the members, as in any Group")

before = v2(*a.meta.position)
c.moveBy(x=2, duration=0.5)
check("member a moved", a.meta.position.x != before.x)
check("nothing rigid on the layer", "Position" not in keysOf(c.layer.meta.index))

# ---------------------------------------------------------------------------
section("composition — one input for anything that wants an index")

check("a Composition reports the layer's index", c.meta.index == c.layer.meta.index)
target = Rectangle(width=4, height=2).matte(c)
check("matte resolves to the layer", target.meta.matteSource == c.layer.meta.index)

# ---------------------------------------------------------------------------
section("composition — the markers are idempotent (autodestroy)")

c.layer.apply(composition())
check("re-marking does not stack twice", keysOf(c.layer.meta.index).count("Composition") == 1)
a.apply(compositionMember(c.layer))
check("re-binding does not stack twice", keysOf(a.meta.index).count("CompositionMember") == 1)

# ---------------------------------------------------------------------------
section("the short name is the same class")
check("`Comp` is the abbreviation, not a second thing", Comp is Composition)

summary()
