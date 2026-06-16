#!/usr/bin/env python3

from __future__ import annotations

from videocode import *


class FocusOn(Circle):
    """
    Manim-inspired `FocusOn`: a translucent circle that starts large and
    transparent, then shrinks onto `(x, y)` while fading in to `color`'s
    opacity — a "spotlight converging on a point" attention cue.
    """

    def __init__(
        self,
        x: wnumber,
        y: wnumber,
        color: rgba = GRAY | 0.2,
        startRadius: wufloat = 3,
        endRadius: wufloat = 0.2,
        start: sec = 0,
        duration: sec = 1.0,
        easing: easing = Easing.Out,
    ):
        super().__init__(radius=startRadius, fillColor=color, strokeColor=TRANSPARENT, strokeWidth=0)
        self.position(x, y)
        self.opacity(0)
        self.fadeIn(easing=easing, duration=duration, from0=True, start=start)
        self.scaleTo(endRadius / startRadius, easing=easing, duration=duration, start=start)
