#!/usr/bin/env python3

from __future__ import annotations

from typing import Any

import svgelements as se

import videocode.input.shape.text._TextHelper as _textHelper
import videocode.utils.logger as logger
from videocode.constants import BLACK, TRANSPARENT, WORLD_TO_SCREEN_RATIO
from videocode.input.shape.svg.SVGPath import SVGPath
from videocode.ty import *


__all__ = [
    "ShapeData",
    "parseSVG",
    "buildPaths",
]


_STEPS = _textHelper._STEPS
_WARN = logger.Logger(prefix="SVG", color=logger.TEXT_GREEN)

type ShapeData = tuple[list[list[point]], rgba, rgba, wufloat]


def _pt(p: Any) -> point:
    return (float(p[0]), float(p[1]))


def _colorToRgba(el: "se.Shape", attr: str) -> rgba:
    """
    `el.fill`/`el.stroke` resolve to a `Color` whose `.value is None` both for
    an explicit `"none"` and for an absent attribute (CSS default already
    applied by svgelements) — in both cases there's nothing to paint, so the
    default is `TRANSPARENT`. The one exception is an unresolvable
    `url(#gradient)` reference (not yet supported — falls back to `BLACK`,
    SVG's own fallback for unresolvable paints).
    """
    color = getattr(el, attr)
    if color is not None and color.value is not None:
        return rgba(color.red, color.green, color.blue, color.alpha)
    values: Any = getattr(el, "values", None)
    raw = values.get(attr, "") if values is not None else ""
    if isinstance(raw, str) and raw.strip().lower().startswith("url("):
        _WARN(f"unsupported {attr}={raw!r} (gradient/pattern reference) — using BLACK")
        return BLACK
    return TRANSPARENT


def _segmentsToContours(segments: list) -> list[list[point]]:
    """
    Split a Path's flattened segment list into per-subpath anchor-handle
    pairs `[a0, h0, a1, h1, ...]` — same format as `_TextHelper.walkContourQuadratics`.

    Line/Close: anchor + midpoint handle. QuadraticBezier: anchor + its
    control point (already the target format). Cubic/Arc: split into
    `_STEPS` quadratic sub-segments, each fit to pass through the
    sub-segment's midpoint (solving the quadratic bezier formula for the
    control point at t=0.5: `control = 2*mid - 0.5*(p0+p2)`) — keeps curves
    smooth (e.g. circles) instead of faceting them into straight chords.
    Each subpath is auto-closed back to its start if it didn't end with
    `Close`.
    """
    contours: list[list[point]] = []
    pairs: list[point] = []
    cur: point = (0.0, 0.0)
    start: point = (0.0, 0.0)

    def line(to: point):
        nonlocal cur
        if to == cur:
            return
        pairs.append(cur)
        pairs.append(((cur[0] + to[0]) / 2, (cur[1] + to[1]) / 2))
        cur = to

    def flush():
        nonlocal pairs
        if cur != start:
            line(start)
        if len(pairs) >= 4 and len(pairs) % 2 == 0:
            contours.append(pairs)
        pairs = []

    for seg in segments:
        if isinstance(seg, se.Move):
            flush()
            cur = start = _pt(seg.end)
        elif isinstance(seg, (se.Line, se.Close)):
            line(_pt(seg.end))
        elif isinstance(seg, se.QuadraticBezier):
            pairs.append(cur)
            pairs.append(_pt(seg.control))
            cur = _pt(seg.end)
        elif isinstance(seg, (se.CubicBezier, se.Arc)):
            p0 = cur
            for s in range(_STEPS):
                t1 = (s + 1) / _STEPS
                tm = (s + 0.5) / _STEPS
                p2 = _pt(seg.point(t1))
                mid = _pt(seg.point(tm))
                control = (2 * mid[0] - 0.5 * (p0[0] + p2[0]), 2 * mid[1] - 0.5 * (p0[1] + p2[1]))
                pairs.append(p0)
                pairs.append(control)
                p0 = p2
            cur = p0

    flush()
    return contours


def parseSVG(filepath: str, width: maybe[wunumber], height: maybe[wunumber]) -> list[ShapeData]:
    svg = se.SVG.parse(filepath)
    svgWidth = float(svg.width or 1)
    svgHeight = float(svg.height or 1)

    if width is not None and height is not None:
        scaleX, scaleY = width / svgWidth, height / svgHeight
    elif width is not None:
        scaleX = scaleY = width / svgWidth
    elif height is not None:
        scaleX = scaleY = height / svgHeight
    else:
        scaleX = scaleY = 1 / WORLD_TO_SCREEN_RATIO

    shapes: list[ShapeData] = []
    for el in svg.elements():
        if not isinstance(el, se.Shape) or isinstance(el, se.SVG):
            continue

        rawContours = _segmentsToContours(se.Path(el).segments())
        if not rawContours:
            continue

        # SVG is y-down, world is y-up. Negating y flips winding, so reverse
        # each contour to restore the stroke-extrusion side convention.
        contours = [
            _textHelper.reversePairs([(x * scaleX, -y * scaleY) for x, y in c])
            for c in rawContours
        ]

        fillColor = _colorToRgba(el, "fill")
        strokeColor = _colorToRgba(el, "stroke")
        strokeWidth = float(el.stroke_width or 0) * (scaleX + scaleY) / 2

        shapes.append((contours, fillColor, strokeColor, strokeWidth))

    return shapes


def buildPaths(
    filepath: str,
    width: maybe[wunumber],
    height: maybe[wunumber],
    fillColor: maybe[rgba] = None,
    strokeColor: maybe[rgba] = None,
    strokeWidth: maybe[wufloat] = None,
) -> list[SVGPath]:
    """
    Parses `filepath` via `parseSVG` and returns each shape as an `SVGPath`
    whose position is set to its bbox center within the SVG canvas — so the
    Group that holds them can apply orbital transforms around the correct pivot.
    """
    paths: list[SVGPath] = []
    for contours, fc, sc, sw in parseSVG(filepath, width, height):
        pts = [p for c in contours for p in c]
        minX, maxX = min(p[0] for p in pts), max(p[0] for p in pts)
        minY, maxY = min(p[1] for p in pts), max(p[1] for p in pts)
        path = SVGPath(
            contours,
            fillColor if fillColor is not None else fc,
            strokeColor if strokeColor is not None else sc,
            strokeWidth if strokeWidth is not None else sw,
        )
        # position = bbox center (align defaults to (0.5, 0.5) in C++)
        path.position((minX + maxX) / 2, (minY + maxY) / 2)
        paths.append(path)

    return paths


