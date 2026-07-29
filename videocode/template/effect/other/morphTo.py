#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator, cast
from weakref import WeakKeyDictionary

from videocode.constants import *
from videocode.shader.ishader import Effect, IShader
from videocode.shader.vertexShader.args import args
from videocode.utils.bezier import *
from videocode.utils.ring import *


if TYPE_CHECKING:
    from videocode.input.input import Input
    from videocode.input.shape.Polygon import Polygon


# Where each shape has been, oldest first — kept HERE, not on the Input. An
# Input's attributes are its public surface; one feature's bookkeeping does not
# belong in it. Weak keys, so a shape that goes out of scope takes its history
# with it instead of leaking one entry per morph.
_history: WeakKeyDictionary[Polygon, list[list[point]]] = WeakKeyDictionary()


def morphTo(
    target: int | list[point],
    *,
    start: sec = 0,
    duration: sec = 2.2,
    easing: easing = Easing.Smooth,
) -> Effect:
    """
    Morph a `Polygon`'s outline, one frame of `points` at a time — `target` is
    either a corner count (a regular polygon of the same area, fitted to the
    current outline) or an explicit ring::

        hexa = Square(side=4, cornerRadius=15)
        hexa.apply(morphTo(6, duration=2.4))       # or hexa.morphTo(6, ...)
        hexa.morphTo(4)                            # back to the SAME square

    A corner count the shape has already been is a RETURN, not a new fit: the
    ring it had then is kept and morphed back to exactly, corner for corner.
    Fitting a fresh square to a hexagon cannot do that — a regular hexagon no
    longer knows it came from a square standing on its corners, so the square
    would come back rotated, which reads as a spin nobody asked for.

    Applied to a `Group`, every member morphs from its own outline.

    `cornerRadius` is resolved on each END shape against its own proportions
    (so a square keeps square-looking corners and a hexagon hexagon-looking
    ones), then the ring AND the per-corner radii are interpolated together and
    the outline is rebuilt each frame.

    That last part is where we beat Manim rather than copy it. Manim can only
    lerp control points, because a VMobject is raw Béziers with no parametric
    description left to re-evaluate — and lerping points folds a corner
    inside-out while it grows out of a flat edge (its arcStart/anchor/arcEnd
    start stacked on one spot and can cross over). We still hold the polygon
    and its radii, so re-rounding an interpolated ring costs nothing and every
    frame is a genuine rounded polygon: measured convex at every t, versus a
    -0.46 fold at t=0.03 for the point-lerp version.

    What we do keep from Manim: resolve the radii on the end shapes, never from
    a percentage read mid-flight — a percentage is relative to an edge length
    that the interpolation is busy changing, which is what made it pop.
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        polygon = cast("Polygon", input)

        src = list(polygon.vertices)

        # A morph away from a ring pushes it; a morph back to that corner count
        # pops it and everything after, so the trip is retraced, not re-derived.
        history: list[list[point]] = list(_history.get(polygon, []))
        seen = next((i for i in reversed(range(len(history))) if len(history[i]) == target), None) if isinstance(target, int) else None

        if seen is not None:
            dst, history = history[seen], history[:seen]
        else:
            # Fitted on the PADDED ring when growing: the vertices about to be
            # inserted are what tells a square which way up its hexagon goes
            # (with the four corners alone the fit is a tie).
            dst = regularRing(growRing(src, max(len(src), target)), target) if isinstance(target, int) else list(target)
            history.append(src)
        _history[polygon] = history

        # radii resolved on each end shape as it stands, before any padding
        srcRadii = cornerRadii(src, polygon.cornerRadius)
        dstRadii = cornerRadii(dst, polygon.cornerRadius)

        # The shape's state once this is over — the target as asked for, not
        # the padded version the interpolation needs: a square that came back
        # from a hexagon is a square again (its two spare vertices are
        # collinear, so they draw the same outline but would keep claiming the
        # shape has six corners).
        endRing = list(dst)

        # Whichever ring has fewer corners gets padded up to the other's count,
        # so a shape can lose corners as readily as it gains them — the ones it
        # loses flatten into an edge instead of vanishing.
        n = max(len(src), len(dst))
        src, srcRadii = growRing(src, n), growRadii(srcRadii, n)
        dst, dstRadii = growRing(dst, n), growRadii(dstRadii, n)
        k = alignOffset(src, dst)
        dst, dstRadii = dst[k:] + dst[:k], dstRadii[k:] + dstRadii[:k]
        matchFlatRadii(src, srcRadii, dst, dstRadii)

        for t, i in easing.rangeIdx(0.0, 1.0, duration):
            ring: list[point] = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(src, dst)]
            radii: list[wunumber] = [a + (b - a) * t for a, b in zip(srcRadii, dstRadii)]
            yield args("points", roundedPoints(ring, radii)).at(start=start + i * SINGLE_FRAME)

        # the ring is the shape's state from here on: the next morph starts from it
        polygon.vertices = endRing

    return _apply
