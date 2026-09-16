#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING
from videocode.constants import *
from videocode.shader.fragmentShader.brightness import brightness as _brightness
from videocode.shader.fragmentShader.crop import crop as _crop
from videocode.shader.vertexShader.hide import hide as _hide
from videocode.shader.vertexShader.opacity import opacity as _opacity
from videocode.shader.vertexShader.position import position as _position
from videocode.shader.vertexShader.scale import scale as _scale
from videocode.shader.vertexShader.show import show as _show
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input

# These orchestrate TWO inputs at once (unlike the rest of template/effect/other/,
# which are single-input Effect factories) — plain functions, not Effect
# callables, since `.apply(effect())` only ever targets one Input.


def crossfade(
    outgoing: Input,
    incoming: Input,
    *,
    start: sec = 0,
    duration: sec = 0.5,
    easing: easing = Easing.InOut,
) -> None:
    """
    Standard crossfade: `outgoing` fades to 0 while `incoming` fades to 255,
    at the same time — the default "Cross Dissolve" of every editor.

        crossfade(sceneA, sceneB, duration=1.0)
    """
    for o, i in easing.rangeIdx(255.0, 0.0, duration):
        outgoing.apply(_opacity(o), start=start + i * SINGLE_FRAME)
    incoming.apply(_show()).apply(_opacity(0), start=start)
    for o, i in easing.rangeIdx(0.0, 255.0, duration):
        incoming.apply(_opacity(o), start=start + i * SINGLE_FRAME)


def push(
    outgoing: Input,
    incoming: Input,
    *,
    direction: Direction = Direction.LEFT,
    distance: wnumber = 2.0,
    start: sec = 0,
    duration: sec = 0.5,
    easing: easing = Easing.InOut,
) -> None:
    """
    Push transition: `outgoing` slides out toward `direction` while
    `incoming` slides in from the opposite side to take its place — as if
    one card pushes the other off-frame. Both inputs' CURRENT positions are
    the destinations/origins (call after positioning them at their resting
    spot).

        push(slide1, slide2, direction=Direction.LEFT, duration=0.6)
    """
    dx, dy = direction.vector
    ox, oy = direction.opposite.vector

    outSrc = v2(*outgoing.meta.position)
    outDst = v2(outSrc.x + dx * distance, outSrc.y + dy * distance)
    inDst = v2(*incoming.meta.position)
    inSrc = v2(inDst.x + ox * distance, inDst.y + oy * distance)

    incoming.apply(_show()).apply(_position(inSrc.x, inSrc.y), start=start)
    for p, i in easing.rangeIdx(outSrc, outDst, duration):
        outgoing.apply(_position(p.x, p.y), start=start + i * SINGLE_FRAME)
    for p, i in easing.rangeIdx(inSrc, inDst, duration):
        incoming.apply(_position(p.x, p.y), start=start + i * SINGLE_FRAME)


def wipeBetween(
    outgoing: Input,
    incoming: Input,
    *,
    direction: Direction = Direction.LEFT,
    start: sec = 0,
    duration: sec = 0.5,
    easing: easing = Easing.InOut,
) -> None:
    """
    Wipe transition: a hard edge sweeps across revealing `incoming` from
    underneath `outgoing`, sweeping toward `direction`. Both inputs should
    already be positioned in the same spot (`incoming` sits behind/below
    `outgoing` — set zIndex if they aren't already stacked correctly).

        wipeBetween(sceneA, sceneB, direction=Direction.RIGHT, duration=0.5)
    """
    side = direction.opposite.side
    incoming.apply(_show()).apply(_crop(**{side: 100.0}), start=start)
    for p, i in easing.rangeIdx(100.0, 0.0, duration):
        incoming.apply(_crop(**{side: p}), start=start + i * SINGLE_FRAME)
    outgoing.apply(_hide(), start=start + duration)


def dipToBlack(
    outgoing: Input,
    incoming: Input,
    *,
    start: sec = 0,
    duration: sec = 0.6,
    easing: easing = Easing.InOut,
) -> None:
    """
    Dip to black: `outgoing` darkens to black over the first half of
    `duration`, then `incoming` rises back up from black over the second
    half — the default transition of every NLE after the straight cut and
    the cross-dissolve.

    Goes through `brightness`, an additive filter, so it can only ever dip
    through black — there is no cheap way to dip through an arbitrary color
    with the shaders this project has.

        dipToBlack(sceneA, sceneB, duration=0.8)
    """
    half = duration / 2
    for b, i in easing.rangeIdx(0.0, -255.0, half):
        outgoing.apply(_brightness(int(b)), start=start + i * SINGLE_FRAME)
    outgoing.apply(_hide(), start=start + half)

    incoming.apply(_show(), start=start + half).apply(_brightness(-255), start=start + half)
    for b, i in easing.rangeIdx(-255.0, 0.0, half):
        incoming.apply(_brightness(int(b)), start=start + half + i * SINGLE_FRAME)


def zoomThrough(
    outgoing: Input,
    incoming: Input,
    *,
    zoom: number = 1.4,
    start: sec = 0,
    duration: sec = 0.5,
    easing: easing = Easing.InOut,
) -> None:
    """
    Zoom transition: `outgoing` scales up by `zoom`x while fading out;
    `incoming` starts scaled up by `zoom`x and settles back to its resting
    scale underneath it — the "zoom transition" preset of CapCut/Premiere.
    Both inputs' CURRENT scale is the resting scale; position `incoming`
    behind `outgoing` (zIndex) so nothing shows through early.

        zoomThrough(clipA, clipB, zoom=1.6, duration=0.4)
    """
    outSrc = v2(*outgoing.meta.scale)
    outDst = outSrc * zoom
    inDst = v2(*incoming.meta.scale)
    inSrc = inDst * zoom

    incoming.apply(_show()).apply(_scale(inSrc.x, inSrc.y), start=start)
    for s, i in easing.rangeIdx(outSrc, outDst, duration):
        outgoing.apply(_scale(s.x, s.y), start=start + i * SINGLE_FRAME)
    for o, i in easing.rangeIdx(255.0, 0.0, duration):
        outgoing.apply(_opacity(o), start=start + i * SINGLE_FRAME)
    for s, i in easing.rangeIdx(inSrc, inDst, duration):
        incoming.apply(_scale(s.x, s.y), start=start + i * SINGLE_FRAME)


def slideOver(
    outgoing: Input,
    incoming: Input,
    *,
    direction: Direction = Direction.LEFT,
    distance: wnumber = 2.0,
    start: sec = 0,
    duration: sec = 0.5,
    easing: easing = Easing.InOut,
) -> None:
    """
    Slide-over transition: `incoming` slides in from `direction` to cover
    `outgoing`, which stays put — unlike `push`, only one input moves.
    `incoming`'s CURRENT position is the destination; position it ABOVE
    `outgoing` (zIndex) so it actually covers it as it arrives.

        slideOver(sceneA, sceneB, direction=Direction.RIGHT, duration=0.4)
    """
    dx, dy = direction.vector
    dst = v2(*incoming.meta.position)
    src = v2(dst.x + dx * distance, dst.y + dy * distance)

    incoming.apply(_show()).apply(_position(src.x, src.y), start=start)
    for p, i in easing.rangeIdx(src, dst, duration):
        incoming.apply(_position(p.x, p.y), start=start + i * SINGLE_FRAME)
