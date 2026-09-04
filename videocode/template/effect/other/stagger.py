#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect

if TYPE_CHECKING:
    from videocode.input.input import Input


def stagger(effect: Effect, *, every: sec = 0.08) -> Effect:
    """
    The same entrance on every member of a group, one beat apart — the
    cascade every editor ships as "stagger" or "sequence".

        Row(*cards, gap=0.3).apply(stagger(popIn(), every=0.08))
        title.apply(stagger(popIn(), every=0.03))   # per letter: a Text IS a Group
        Row(*bars).apply(stagger(slideIn(direction=Direction.BOTTOM), every=0.05))

    `Group.apply` dispatches an `Effect` once per member, in order, and this
    wrapper counts those calls: the n-th member's shaders all start `n * every`
    later than the effect wrote them. `every=0` is the plain effect. The last
    member ends last, so a following `flush()` or `wait()` waits for the whole
    cascade.

    A wrapper cannot see the `start=` of the `apply()` it runs inside, so a
    shader the effect left untimed is taken from 0 — where every effect in
    this package already puts its own timing.

    Not for `typewriter`, which hides every letter on the SAME frame before
    revealing them in turn; shifted, that hide would leave each letter visible
    until its beat.
    """
    index = 0

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        nonlocal index
        delay = index * every
        index += 1
        for s in effect(input):
            s.start = (s.start or 0) + delay
            yield s

    return _apply
