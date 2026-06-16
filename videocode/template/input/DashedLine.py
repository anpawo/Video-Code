#!/usr/bin/env python3

from __future__ import annotations

import math

from videocode import *


class DashedLine(Group[HorizontalLine]):
    """
    Manim-inspired `DashedLine`: a straight line from `(x1, y1)` to
    `(x2, y2)` rendered as a series of evenly-spaced dashes — handy for
    annotation/helper lines (e.g. extending a measurement, indicating a
    hidden edge).

    `dashLength` is the period (dash + gap); `dashedRatio` is the fraction
    of each period drawn as a dash (`0.5` = equal dash/gap).
    """

    def __init__(
        self,
        x1: wnumber,
        y1: wnumber,
        x2: wnumber,
        y2: wnumber,
        dashLength: wufloat = 0.16,
        dashedRatio: percent = 50,
        color: rgba = WHITE,
        strokeWidth: wufloat = 0.05,
    ):
        dx, dy = x2 - x1, y2 - y1
        totalLength = math.hypot(dx, dy)
        angle = math.degrees(math.atan2(dy, dx))
        n = max(1, round(totalLength / dashLength))
        segmentLength = dashLength * (dashedRatio / 100)

        dashes: list[HorizontalLine] = []
        for i in range(n):
            t = (i + 0.5) / n
            dash = HorizontalLine(
                length=segmentLength,
                strokeWidth=strokeWidth,
                fillColor=color,
                strokeColor=TRANSPARENT,
                rounded=True,
            ).rotation(angle)
            dash.position(x1 + dx * t, y1 + dy * t)
            dashes.append(dash)

        super().__init__(*dashes)
