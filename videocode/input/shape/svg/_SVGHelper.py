#!/usr/bin/env python3

from __future__ import annotations

import xml.etree.ElementTree as ET
from math import atan2, degrees
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


def _stopField(stop: ET.Element, name: str, fallback: str) -> str:
    """`style="stop-color:red"` beats the presentation attribute — every exporter writes one or the other."""
    style = dict(
        (k.strip(), v.strip()) for k, _, v in (d.partition(":") for d in stop.get("style", "").split(";"))
    )
    return style.get(name) or stop.get(name) or fallback


def _percent(raw: str) -> float:
    raw = raw.strip()
    return float(raw[:-1]) if raw.endswith("%") else float(raw) * 100


def _parseGradients(filepath: str) -> dict[str, rgba]:
    """
    Maps every `<linearGradient>`/`<radialGradient>` id in the file to the
    engine gradient it means, so `fill="url(#sunset)"` can be resolved.

    `svgelements` is no help here: it has no gradient class at all, never
    yields `<defs>` children from `elements()`, and hands back a `Color`
    already flattened to opaque black for any `url(...)` paint — so the stops
    have to be read off the raw XML, once per file.

    A gradient whose id is missing from this map is one this parser refuses:
    the caller warns and falls back to `BLACK`, SVG's own fallback for an
    unresolvable paint.

    Ceiling worth knowing even for what IS supported: the engine spreads a
    gradient across the shape's extent along its axis, which equals SVG's
    `objectBoundingBox` only when the axis is horizontal or vertical. A
    diagonal gradient lands slightly off what a browser draws.
    """
    gradients: dict[str, rgba] = {}
    for el in ET.parse(filepath).getroot().iter():
        kind = el.tag.rsplit("}", 1)[-1]
        if kind not in ("linearGradient", "radialGradient"):
            continue
        gid = el.get("id")
        # ponytail: `gradientTransform`, user-space coordinates and `href` stop
        # inheritance are dropped rather than half-honoured — a gradient placed
        # in the wrong space is a worse lie than an admitted black. Resolve the
        # transform into the stop axis if a real file ever needs it.
        if gid is None or el.get("gradientTransform") is not None:
            continue
        if el.get("gradientUnits", "objectBoundingBox") != "objectBoundingBox":
            continue
        if el.get("href") is not None or el.get("{http://www.w3.org/1999/xlink}href") is not None:
            continue

        stops: list[rgba | tuple[rgba, percent]] = []
        for stop in el:
            if stop.tag.rsplit("}", 1)[-1] != "stop":
                continue
            # `stop-color="none"` is not a color: svgelements answers None to
            # every component, which would crash the multiply below.
            color: Any = se.Color(_stopField(stop, "stop-color", "#000000"))
            if color.value is None:
                color = se.Color("#000000")
            alpha = round(color.alpha * float(_stopField(stop, "stop-opacity", "1")))
            stops.append((rgba(color.red, color.green, color.blue, alpha), _percent(stop.get("offset", "0"))))
        if len(stops) < 2:
            continue

        if kind == "radialGradient":
            gradients[gid] = RadialGradient(*stops)
        else:
            x1, y1 = _percent(el.get("x1", "0")) / 100, _percent(el.get("y1", "0")) / 100
            x2, y2 = _percent(el.get("x2", "1")) / 100, _percent(el.get("y2", "0")) / 100
            # SVG's y points down, the engine's 90 is bottom -> top: flip dy.
            gradients[gid] = LinearGradient(*stops, angle=degrees(atan2(y1 - y2, x2 - x1)))
    return gradients


def _colorToRgba(el: "se.Shape", attr: str, gradients: dict[str, rgba]) -> rgba:
    """
    The raw attribute is read before `el.fill`/`el.stroke` because svgelements
    resolves `url(#g)` to an opaque black `Color` — indistinguishable from a
    real `fill="#000"` by the time the property is asked.

    Otherwise: a `Color` whose `.value is None` means both an explicit `"none"`
    and an absent attribute (CSS default already applied by svgelements) — in
    both cases there's nothing to paint, so the default is `TRANSPARENT`.
    """
    values: Any = getattr(el, "values", None)
    raw = values.get(attr, "") if values is not None else ""
    if isinstance(raw, str) and raw.strip().lower().startswith("url("):
        reference = raw.strip()[4:].split(")")[0].strip().strip("\"'").lstrip("#")
        gradient = gradients.get(reference)
        if gradient is not None:
            return gradient
        _WARN(f"unsupported {attr}={raw!r} (unresolved gradient/pattern reference) — using BLACK")
        return BLACK
    color = getattr(el, attr)
    if color is not None and color.value is not None:
        return rgba(color.red, color.green, color.blue, color.alpha)
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
    gradients = _parseGradients(filepath)
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

        fillColor = _colorToRgba(el, "fill", gradients)
        strokeColor = _colorToRgba(el, "stroke", gradients)
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


