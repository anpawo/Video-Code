#!/usr/bin/env python3


from __future__ import annotations

import subprocess
import freetype
from functools import cache
from uharfbuzz import Blob as HBBlob, Font as HBFont, Face as HBFace, Buffer as HBBuffer, shape as hb_shape  # type: ignore[import-untyped]

from pathlib import Path
from videocode.input.interface.Offset import Offset
from videocode.ty import *
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from videocode.input.shape.text.Text import Letter


_FONT_DIR = Path(__file__).parents[3] / "assets" / "fonts"
_STEPS = 4
_FT_FLAGS = 1 | 2 | 8  # FT_LOAD_NO_SCALE | FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP


@cache
def fontPath(family: str, bold: bool, italic: bool) -> str:
    styles = ["BoldItalic", "Bold-Italic", "Bold_Italic"] if bold and italic else ["Bold"] if bold else ["Italic"] if italic else ["Regular", ""]
    if _FONT_DIR.is_dir():
        for style in styles:
            for ext in (".ttf", ".otf"):
                for sep in ("-", " ", "_", ""):
                    p = _FONT_DIR / f"{family}{sep}{style}{ext}"
                    if p.exists():
                        return str(p)
    fc_style = "Bold Italic" if bold and italic else "Bold" if bold else "Italic" if italic else "Regular"
    try:
        r = subprocess.run(
            ["fc-match", f"{family}:style={fc_style}", "--format=%{file}"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    raise FileNotFoundError(f"Font not found: {family!r} bold={bold} italic={italic}")


@cache
def loadFaces(path: str) -> tuple[freetype.Face, Any, int, float, tuple[float, float]]:
    ft = freetype.Face(path)
    upem = ft.units_per_EM
    blob = HBBlob(Path(path).read_bytes())
    hb_font = HBFont(HBFace(blob))
    hb_font.scale = (upem, upem)

    # Get cap height (keep existing code)
    try:
        ft.load_char(ord("H"), _FT_FLAGS)
        pts = ft.glyph.outline.points
        capH = float(max(p[1] for p in pts)) if pts else float(upem) * 0.7
    except Exception:
        capH = float(upem) * 0.7

    return ft, hb_font, upem, capH, (float(ft.descender), float(ft.ascender))


def shape(text: str, hb_font: Any, features: dict[str, bool] | None = None) -> tuple[list, list]:
    buf = HBBuffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb_shape(hb_font, buf, features or {})
    return buf.glyph_infos, buf.glyph_positions


def walkContourQuadratics(rawPts: list, tags: list[int]) -> list[tuple[float, float]]:
    """
    Closed anchor-handle pairs [a0, h0, a1, h1, …] from one FreeType contour.

    Conic (TrueType quadratic) segments pass through as TRUE quadratics — the
    renderer tessellates them adaptively to on-screen pixel size, so glyphs
    stay smooth at any fontSize (fixed-step sampling left visible kinks on big
    letters). Straight segments get midpoint handles; cubic segments (CFF
    fonts) are still sampled at _STEPS and emitted as straight pairs.
    """
    n = len(rawPts)
    if n < 2:
        return []
    pts = [(float(p[0]), float(p[1])) for p in rawPts]
    tg = [t & 3 for t in tags]
    ON, CONIC, CUBIC = 1, 0, 2

    start = next((k for k in range(n) if tg[k] == ON), None)
    if start is None:
        # All-off-curve contour (TrueType allows it): the implied on-curve
        # midpoint between the last and first control points starts the path.
        pts = [((pts[-1][0] + pts[0][0]) / 2, (pts[-1][1] + pts[0][1]) / 2)] + pts
        tg = [ON] + tg
        n += 1
        start = 0
    pts = pts[start:] + pts[:start]
    tg = tg[start:] + tg[:start]

    pairs: list[tuple[float, float]] = []
    cur = pts[0]

    def line(to: tuple[float, float]):
        nonlocal cur
        if to == cur:
            return
        pairs.append(cur)
        pairs.append(((cur[0] + to[0]) / 2, (cur[1] + to[1]) / 2))
        cur = to

    i = 1
    while i < n:
        if tg[i] == ON:
            line(pts[i])
            i += 1
        elif tg[i] == CUBIC and i + 2 < n:
            x0, y0 = cur
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            x3, y3 = (
                pts[i + 2]
                if tg[i + 2] == ON
                else (
                    (pts[i + 1][0] + pts[(i + 2) % n][0]) / 2,
                    (pts[i + 1][1] + pts[(i + 2) % n][1]) / 2,
                )
            )
            for s in range(1, _STEPS + 1):
                t = s / _STEPS
                mt = 1 - t
                line(
                    (
                        mt**3 * x0 + 3 * mt**2 * t * x1 + 3 * mt * t**2 * x2 + t**3 * x3,
                        mt**3 * y0 + 3 * mt**2 * t * y1 + 3 * mt * t**2 * y2 + t**3 * y3,
                    )
                )
            i += 3 if i + 2 < n and tg[i + 2] == ON else 2
        else:  # CONIC run (or stray CUBIC tag)
            ctrls: list[tuple[float, float]] = [pts[i]]
            j = i + 1
            while j < n and tg[j] == CONIC:
                ctrls.append(pts[j])
                j += 1
            # The run ends on the next on-curve point, or closes back to the
            # contour start when the conic is the trailing segment.
            endPt = pts[j] if j < n else pts[0]
            for k, ctrl in enumerate(ctrls):
                nxt = ((ctrl[0] + ctrls[k + 1][0]) / 2, (ctrl[1] + ctrls[k + 1][1]) / 2) if k < len(ctrls) - 1 else endPt
                pairs.append(cur)
                pairs.append(ctrl)
                cur = nxt
            i = j + (1 if j < n and tg[j] == ON else 0)

    # Close the path back to the first anchor with a straight segment if the
    # walk didn't already end there (conic closures end exactly at pts[0]).
    line(pts[0])
    return pairs


@cache
def _glyphContours(path: str, glyphId: int) -> tuple[tuple[tuple[float, float], ...], ...]:
    """
    Unscaled per-contour control points (anchor-handle pairs) in font units.

    Contours stay separate — the renderer fills outer+holes via earcut-with-holes
    and strokes each contour on its own, so no bridge edges exist to be stroked
    or to break at partial opacity.
    """
    ft, *_ = loadFaces(path)
    ft.load_glyph(glyphId, _FT_FLAGS)
    ol = ft.glyph.outline
    if not ol.points:
        return ()
    raw = list(ol.points)
    tags = list(ol.tags)
    ends = list(ol.contours)
    contours: list[tuple[tuple[float, float], ...]] = []
    start = 0
    for end in ends:
        pairs = walkContourQuadratics(raw[start : end + 1], tags[start : end + 1])
        if len(pairs) >= 6:
            # Reversed to keep the same winding the legacy vertex pathway
            # produced (it iterated reversed(verts)) — stroke extrusion
            # direction depends on it.
            contours.append(tuple(reversePairs(pairs)))
        start = end + 1
    return tuple(contours)


def _glyphVerts(path: str, glyphId: int) -> list[tuple[float, float]]:
    """Flattened control points across all contours — bbox/min computations only."""
    return [p for c in _glyphContours(path, glyphId) for p in c]


def reversePairs(pairs: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """
    Reverse the winding of a closed anchor-handle pair list.

    With anchors A0..Am-1 and handles H0..Hm-1 (Hi sits between Ai and Ai+1),
    the reversed path is [A0, Hm-1, Am-1, Hm-2, …, A1, H0] — same curves,
    opposite traversal direction.
    """
    anchors = pairs[0::2]
    handles = pairs[1::2]
    m = len(anchors)
    out: list[tuple[float, float]] = [anchors[0]]
    for k in range(1, m):
        out.append(handles[m - k])
        out.append(anchors[m - k])
    out.append(handles[0])
    return out


@cache
def buildLetterData(
    text: str,
    fontSize: float,
    fontFamily: str,
    bold: bool,
    italic: bool,
) -> list[tuple[str, float, float]]:
    """
    Returns (char, x_offset, y_offset) for each rendered glyph.
    """
    path = fontPath(fontFamily, bold, italic)
    _, hbFont, _, capH, __ = loadFaces(path)
    scale = fontSize / capH

    infos, positions = shape(text, hbFont)
    result: list[tuple[str, float, float]] = []
    cx = cy = 0.0

    for info, pos in zip(infos, positions):
        xOff = cx + pos.x_offset * scale
        yOff = cy + pos.y_offset * scale
        cached = _glyphVerts(path, info.codepoint)
        if cached:
            verts = [(x * scale, y * scale) for x, y in cached]
            char = text[info.cluster] if info.cluster < len(text) else ""
            result.append((char, xOff + min(v[0] for v in verts), yOff + min(v[1] for v in verts)))
        cx += pos.x_advance * scale
        cy += pos.y_advance * scale

    return result


@cache
def lineAnchor(fontFamily: str, bold: bool, italic: bool, fontSize: float, alignY: float) -> float:
    path = fontPath(fontFamily, bold, italic)
    _, _, _, capH, (desc, asc) = loadFaces(path)
    scale = fontSize / capH
    return desc * scale + alignY * (asc - desc) * scale


def buildLetters(
    text: str,
    fontSize: float,
    fontFamily: str,
    bold: bool,
    italic: bool,
    fillColor: rgba,
    strokeColor: rgba,
    strokeWidth: float,
) -> list[Offset[Letter]]:
    from videocode.input.shape.text.Text import Letter

    letters: list[Offset[Letter]] = []
    for char, x, y in buildLetterData(text, fontSize, fontFamily, bold, italic):
        letter = Letter(
            char=char,
            fontSize=fontSize,
            fontFamily=fontFamily,
            bold=bold,
            italic=italic,
            fillColor=fillColor,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
        )
        letters.append(Offset(letter, x=x, y=y))

    return letters
