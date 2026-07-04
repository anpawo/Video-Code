#!/usr/bin/env python3

from __future__ import annotations

import math

from videocode import *
from videocode.shader.vertexShader.position import position as _position

__all__ = ["CompoundPolygon"]


class CompoundPolygon(Polygon):
    """
    Batches multiple same-material Polygon instances into a single C++ input.

    Members must be created inside a ``Context.noRegister()`` block — they are
    never individually registered with C++.  The CompoundPolygon itself is one
    Polygon whose geometry is the union of all member contours, each offset to
    world space by the member's position at construction time.

    Usage::

        with Context.noRegister():
            lines = [VerticalLine(length=10).position(x=i) for i in range(-5, 6)]
        grid = CompoundPolygon(*lines)

    The :meth:`drift` method animates the entire compound polygon with a tiled
    scroll, equivalent to per-element drift but using a single position shader
    per frame instead of one per element.
    """

    def __init__(self, *members: Polygon) -> None:
        if not members:
            raise ValueError("CompoundPolygon requires at least one member")

        all_contours: list[list[point]] = []

        for m in members:
            ox, oy = m.meta.position.x, m.meta.position.y
            pts = m.points
            sizes: list[int] = list(m.contourSizes) if m.contourSizes else [len(pts)]
            base = 0
            for size in sizes:
                chunk = pts[base : base + size]
                all_contours.append([(p[0] + ox, p[1] + oy) for p in chunk])
                base += size

        self._all_contours = all_contours

        super().__init__(
            vertices=[],
            fillColor=members[0].fillColor,
            strokeColor=members[0].strokeColor,
            strokeWidth=members[0].strokeWidth,
        )

    # ------------------------------------------------------------------
    # Polygon overrides

    def generateRawContours(self) -> list[list[point]]:
        return self._all_contours

    def generateVertices(self) -> list[point]:
        return [p for c in self._all_contours for p in c]

    @property
    def width(self) -> wunumber:
        xs = [p[0] for c in self._all_contours for p in c]
        return (max(xs) - min(xs)) if xs else 0

    @property
    def height(self) -> wunumber:
        ys = [p[1] for c in self._all_contours for p in c]
        return (max(ys) - min(ys)) if ys else 0

    # ------------------------------------------------------------------
    # Drift

    def drift(
        self,
        dx: wnumber = -0.5,
        dy: wnumber = 0.25,
        duration: maybe[sec] = None,
    ) -> Self:
        """
        Animate the compound polygon with a seamlessly tiling scroll.

        All member contours share the same drift vector, so the whole polygon
        shifts by ``fmod(progress * dx * dur/2, tile)`` each frame.
        This is equivalent to per-element drift but uses one position shader
        per frame instead of one per element, and benefits from the mesh cache
        (position-only change → no earcut per drift frame).
        """
        tile = 1 / 3
        dur = Context.lastEverAffectedFrame * SINGLE_FRAME if duration is None else duration
        n = int(dur * FRAMERATE)

        for i in range(n):
            progress = i / n if n > 0 else 0
            off_x = math.fmod(progress * dx * dur * 0.5, tile)
            off_y = math.fmod(progress * dy * dur * 0.5, tile)
            self.apply(_position(off_x, off_y), start=i * SINGLE_FRAME, duration=SINGLE_FRAME, offset=0)

        return self
