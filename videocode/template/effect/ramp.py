#!/usr/bin/env python3

from __future__ import annotations

from typing import Any, Generator

from videocode.constants import *
from videocode.utils.bezier import *


def dipAndReturn(
    *,
    peak: number,
    start: sec = 0,
    duration: sec = 2.0,
    fade: sec = 0.4,
    rise: easing = Easing.Out,
    fall: easing = Easing.In,
) -> Generator[tuple[float, sec], Any, None]:
    """
    The three-phase ramp a "grade" effect follows: climb from 0 to `peak` over
    `fade`, HOLD there, then come back down to 0 over `fade`. Yields
    `(value, time)` pairs, one per frame, `time` being an offset in seconds to
    hand to `IShader.at(start=...)`.

    Why one pair PER FRAME through the hold, and not a single pair for the
    whole plateau: a fragment shader posed on a frame only applies to that
    frame. Emitting the plateau once left `duration - 2 * fade` seconds with
    no emission at all, and the effect vanished between its entrance and its
    exit — a 2 s `spotlightOn` was visible for 0.35 s, dark for 1.3 s, then
    visible again. Costs one shader per frame, which is what every other
    animated template already pays.

    `fade` is clamped to half of `duration`, so `fade >= duration / 2` gives a
    straight dip with no plateau.

        for v, t in dipAndReturn(peak=0.8, duration=2.0, fade=0.35):
            yield vignette(v).at(start=t)
    """
    f = min(fade, duration / 2)

    for v, i in rise.rangeIdx(0.0, float(peak), f):
        yield v, start + i * SINGLE_FRAME

    hold = duration - 2 * f
    if hold > 0:
        for i in range(round(hold * FRAMERATE)):
            yield float(peak), start + f + i * SINGLE_FRAME

    for v, i in fall.rangeIdx(float(peak), 0.0, f):
        yield v, start + duration - f + i * SINGLE_FRAME
