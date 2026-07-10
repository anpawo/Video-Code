#!/usr/bin/env python3

from __future__ import annotations

import math

from videocode.input.shape.Polygon import Polygon, paint
from videocode.utils.decorators import prop
from videocode.ty import *
from videocode.constants import *


class Circle(Polygon):
    """
    A circle approximated by quadratic bezier segments — a `Polygon` whose
    control points are generated directly (raw contour), so it gets the full
    polygon pipeline: geometry cache, gradients, zIndex, effects.
    """

    def __init__(
        self,
        radius: wufloat = 1,
        fillColor: paint = RED_A,
        strokeColor: rgba = WHITE,
        strokeWidth: wufloat = 0.05,
    ):
        self.radius = radius
        super().__init__(
            vertices=self.generateVertices(),
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
        )

    def generateRawContours(self) -> list[list[point]]:
        # These points are already final bezier anchor/handle pairs, so this
        # bypasses Polygon's default corner-rounding (which expects one plain
        # vertex per corner and emits 4 bezier points per corner — it would
        # mangle an already-bezier contour like this one).
        #
        # Manim's formula: anchors on the circle; handles at the mid-arc angle,
        # scaled outward by 1/cos(segAngle/2) (the tangent-intersection point).
        # Emitted clockwise (negative sin) so the pixel-space winding after the
        # renderer's y-negation matches the other polygons.
        N = 16
        segAngle = 2 * math.pi / N
        cosHalf = math.cos(segAngle / 2)
        r = self.radius

        pts: list[point] = []
        for i in range(N):
            aAngle = i * segAngle
            hAngle = aAngle + segAngle / 2
            pts.append((r * math.cos(aAngle), -r * math.sin(aAngle)))
            pts.append((r / cosHalf * math.cos(hAngle), -r / cosHalf * math.sin(hAngle)))
        return [pts]

    def generateVertices(self) -> list[point]:
        # Required by Polygon (used for width/height/contains-point checks).
        # Circle has no separate "corner vertex" representation, so this just
        # reuses the same raw contour points as generateRawContours.
        return list(self.generateRawContours()[0])

    @prop(onSet=Polygon.updatePoints)
    def radius() -> wufloat: ...


class Dot(Circle):
    def __init__(
        self,
        radius: float = 0.0375,
        fillColor: paint = RED_A,
    ):
        super().__init__(
            radius=radius,
            fillColor=fillColor,
            strokeColor=TRANSPARENT,
            strokeWidth=0,
        )
