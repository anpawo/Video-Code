#!/usr/bin/env python3

"""
Vertex-ring math: pure geometry on ``list[point]``, no Input involved.

A ring is a closed polygon given as its corners, in order — the same list a
``Polygon`` keeps in ``vertices``. These helpers resample it, fit a regular
polygon to it, and turn it into the anchor/handle control points the C++ side
draws. Everything here is dependency-free and testable without rendering.
"""

from __future__ import annotations

import math

from videocode.ty import *


__all__ = [
    "insertionCounts",
    "growRing",
    "growRadii",
    "cornerRadii",
    "matchFlatRadii",
    "regularRing",
    "alignOffset",
    "isFlat",
    "roundedPoints",
]


def insertionCounts(m: int, extra: int) -> list[int]:
    """
    How many vertices to insert on each of `m` edges to add `extra` in total,
    spread as evenly as possible (Manim's insert_n_curves does the same with
    the same integer-division trick).
    """
    counts = [0] * m
    for j in range(extra):
        counts[(j * m) // extra] += 1
    return counts


def growRing(vertices: list[point], n: int) -> list[point]:
    """
    The same outline with `n` vertices — the extra ones are inserted along the
    edges. The silhouette is untouched (they are collinear), which is what
    makes a 4 -> 6 morph well defined: both rings end up the same length, so
    corner i simply travels to corner i.
    """
    m = len(vertices)
    if n < m:
        raise ValueError(f"cannot grow a {m}-gon down to {n} vertices")
    counts = insertionCounts(m, n - m)

    ring: list[point] = []
    for i, v in enumerate(vertices):
        nxt = vertices[(i + 1) % m]
        ring.append(v)
        for k in range(1, counts[i] + 1):
            t = k / (counts[i] + 1)
            ring.append((v[0] + (nxt[0] - v[0]) * t, v[1] + (nxt[1] - v[1]) * t))
    return ring


def cornerRadii(ring: list[point], percent: percent) -> list[wunumber]:
    """
    ``cornerRadius`` resolved to world units, corner by corner — the library's
    own rule: a percentage of the corner's half-edge, so a big shape rounds
    proportionally more than a small one.

    Resolve it on the shape you actually want to look at, BEFORE growing the
    ring: inserting a vertex halves an edge, and a percentage read after that
    would halve the radius of the two corners around it.
    """
    n = len(ring)
    return [percent / 100 * 0.5 * min(math.dist(ring[i], ring[i - 1]), math.dist(ring[i], ring[(i + 1) % n])) for i in range(n)]


def growRadii(radii: list[wunumber], n: int) -> list[wunumber]:
    """
    `radii` padded to `n` the same way growRing pads a ring — the inserted
    corners are flat, so they get no rounding (see matchFlatRadii).
    """
    counts = insertionCounts(len(radii), n - len(radii))
    grown: list[wunumber] = []
    for r, c in zip(radii, counts):
        grown.append(r)
        grown.extend([0.0] * c)
    return grown


def isFlat(ring: list[point], i: int, eps: float = 1e-9) -> bool:
    """Whether corner `i` is a straight-through vertex (an inserted one)."""
    n = len(ring)
    prev, here, nxt = ring[i - 1], ring[i], ring[(i + 1) % n]
    cross = (here[0] - prev[0]) * (nxt[1] - here[1]) - (here[1] - prev[1]) * (nxt[0] - here[0])
    return abs(cross) < eps


def matchFlatRadii(srcRing: list[point], srcRadii: list[wunumber], dstRing: list[point], dstRadii: list[wunumber]) -> None:
    """
    Give every flat corner the radius the other end uses at that index, in
    place — so a corner growing out of a flat edge has its final radius from
    its very first frame instead of ramping up from 0 and looking sharp the
    whole way out (and the same on the way back in).

    Free of charge: a flat corner draws the same straight line whatever its
    radius (its three control points stay collinear), so neither end shape
    changes. Only the corners in between do.
    """
    src, dst = list(srcRadii), list(dstRadii)
    for i in range(len(srcRing)):
        if isFlat(srcRing, i):
            srcRadii[i] = dst[i]
        if isFlat(dstRing, i):
            dstRadii[i] = src[i]


def regularRing(vertices: list[point], sides: maybe[int] = None) -> list[point]:
    """
    The regular polygon fitted to `vertices`: same centroid, same area, and the
    orientation that best matches the corners already there — so the target
    lines up with the ring instead of the ring spinning into it.

    `sides` defaults to the ring's own corner count, but any count works, in
    either direction: the orientation comes from the n-fold circular mean of
    the corner angles (`atan2(Σ sin nθ, Σ cos nθ) / n`), which needs no
    correspondence between the two rings. That is what lets a hexagon morph
    down to a square as readily as a square morphs up to a hexagon.

    Same area, not same radius: Manim's RegularPolygon takes a circumradius,
    which makes a hexagon and an octagon of equal `radius` look like different
    sizes — wrong when one is morphing into the other.
    """
    m = len(vertices)
    n = sides if sides is not None else m
    cx = sum(v[0] for v in vertices) / m
    cy = sum(v[1] for v in vertices) / m

    shoelace = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(vertices, vertices[1:] + vertices[:1]))
    radius = math.sqrt(abs(shoelace) / (n * math.sin(2 * math.pi / n)))

    angles = [math.atan2(v[1] - cy, v[0] - cx) for v in vertices]
    ss = sum(math.sin(n * a) for a in angles)
    cs = sum(math.cos(n * a) for a in angles)
    # A square has no preferred 6-fold orientation, a hexagon no preferred
    # 4-fold one: the sum cancels and atan2 would answer 0 — an arbitrary
    # orientation that reads as a spin. Line the first corner up instead, so
    # the answer stays deterministic and the ring keeps its footing.
    phase = math.atan2(ss, cs) / n if math.hypot(ss, cs) > 1e-6 * m else angles[0]

    step = 2 * math.pi / n
    return [(cx + radius * math.cos(phase + i * step), cy + radius * math.sin(phase + i * step)) for i in range(n)]


def alignOffset(ring: list[point], target: list[point]) -> int:
    """
    The cyclic offset that brings `target` closest to `ring`, so corner i has
    the shortest possible trip and the shape doesn't spin on its way there.
    Manim has no equivalent — it pairs points by index and leaves you to roll
    them yourself when the result spins.
    """
    n = len(ring)
    return min(range(n), key=lambda k: sum(math.dist(v, target[(i + k) % n]) ** 2 for i, v in enumerate(ring)))


def roundedPoints(ring: list[point], radii: list[wunumber]) -> list[point]:
    """
    Polygon.buildPoints' closed-path rounding, but taking one radius per corner
    in world units (from cornerRadii) instead of one global percentage — same
    4-point output (arcStart, cornerHandle, arcEnd, connectorMidpoint) in the
    same reversed order, so it drops straight into ``points``.

    Per corner is what lets a grown ring keep the outline it had: the corners
    that were already there keep their radius, the inserted ones get 0 and stay
    flat. A single percentage cannot express that — it is read against each
    corner's own half-edge, which the insertion has just changed.
    """
    rev = list(reversed(ring))
    revRadii = list(reversed(radii))
    n = len(rev)

    def unit(a: point, b: point) -> point:
        d = math.dist(a, b)
        return ((b[0] - a[0]) / d, (b[1] - a[1]) / d) if d > 1e-9 else (0.0, 0.0)

    arcStart: list[point] = []
    arcEnd: list[point] = []
    for i in range(n):
        prev, nxt = rev[i - 1], rev[(i + 1) % n]
        r = min(revRadii[i], 0.5 * math.dist(rev[i], prev), 0.5 * math.dist(rev[i], nxt))
        uIn, uOut = unit(rev[i], prev), unit(rev[i], nxt)
        arcStart.append((rev[i][0] + uIn[0] * r, rev[i][1] + uIn[1] * r))
        arcEnd.append((rev[i][0] + uOut[0] * r, rev[i][1] + uOut[1] * r))

    points: list[point] = []
    for i in range(n):
        nxt = (i + 1) % n
        points.append(arcStart[i])
        points.append(rev[i])
        points.append(arcEnd[i])
        points.append(((arcEnd[i][0] + arcStart[nxt][0]) / 2, (arcEnd[i][1] + arcStart[nxt][1]) / 2))
    return points
