#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING
import videocode.constants as _constants
from videocode.color import RadialGradient
from videocode.constants import *
from videocode.shader.fragmentShader.blur import blur as _blur
from videocode.shader.fragmentShader.brightness import brightness as _brightness
from videocode.shader.fragmentShader.crop import crop as _crop
from videocode.shader.fragmentShader.glitch import glitch as _glitch
from videocode.shader.vertexShader.blendMode import BlendMode
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
    _dipThrough(outgoing, incoming, -255.0, start, duration, easing)


def flash(
    outgoing: Input,
    incoming: Input,
    *,
    start: sec = 0,
    duration: sec = 0.4,
    easing: easing = Easing.InOut,
) -> None:
    """
    Flash: `outgoing` burns up to white, and `incoming` comes down out of it —
    `dipToBlack` through white, the camera-flash cut of an edit that wants a
    beat to land.

        flash(clipA, clipB, duration=0.3)
    """
    _dipThrough(outgoing, incoming, 255.0, start, duration, easing)


def _dipThrough(outgoing: Input, incoming: Input, level: float, start: sec, duration: sec, easing: easing) -> None:
    half = duration / 2
    for b, i in easing.rangeIdx(0.0, level, half):
        outgoing.apply(_brightness(int(b)), start=start + i * SINGLE_FRAME)
    outgoing.apply(_hide(), start=start + half)

    incoming.apply(_show(), start=start + half).apply(_brightness(int(level)), start=start + half)
    for b, i in easing.rangeIdx(level, 0.0, half):
        incoming.apply(_brightness(int(b)), start=start + half + i * SINGLE_FRAME)


def whipPan(
    outgoing: Input,
    incoming: Input,
    *,
    direction: Direction = Direction.LEFT,
    distance: maybe[wnumber] = None,
    blurStrength: unumber = 31,
    start: sec = 0,
    duration: sec = 0.35,
    easing: easing = Easing.InOut,
) -> None:
    """
    Whip pan: a `push` a whole frame wide (`distance` defaults to the frame's
    width) and fast, both inputs smeared by a blur that peaks at the cut — the
    swish pan, where the camera snaps between two shots too fast to read.

    There is no motion blur between frames (docs/FEATURES_TODO.md §5): the
    smear is a plain blur, strong enough at that speed to read as one. Both
    inputs' CURRENT positions are the resting spots, as for `push`.

        whipPan(clipA, clipB, direction=Direction.LEFT, duration=0.3)
    """
    push(outgoing, incoming, direction=direction, distance=distance or _constants.WORLD_WIDTH, start=start, duration=duration, easing=easing)
    half = duration / 2
    odd = lambda s: 2 * int(s / 2) + 1  # blur takes an odd kernel; 1 is no blur
    for s, i in easing.rangeIdx(1.0, blurStrength, half):
        outgoing.apply(_blur(odd(s)), start=start + i * SINGLE_FRAME)
    incoming.apply(_blur(odd(blurStrength)), start=start)
    for s, i in easing.rangeIdx(blurStrength, 1.0, half):
        incoming.apply(_blur(odd(s)), start=start + half + i * SINGLE_FRAME)


def glitchCut(
    outgoing: Input,
    incoming: Input,
    *,
    amount: percent = 4,
    start: sec = 0,
    duration: sec = 0.4,
    seed: number = 7,
) -> None:
    """
    Glitch cut: `outgoing` tears into sideways slices, the cut lands in the
    middle of the tear, and `incoming` tears back into place — the "mask
    glitch" of short-form edits. `seed` is fixed so the same scene always
    tears the same way.

        glitchCut(clipA, clipB, amount=6, duration=0.3)
    """
    half = duration / 2
    outgoing.apply(_glitch(amount=amount, seed=seed), start=start, duration=half)
    outgoing.apply(_hide(), start=start + half)
    incoming.apply(_show(), start=start + half)
    incoming.apply(_glitch(amount=amount, seed=seed + 1), start=start + half, duration=half)


def filmBurn(
    outgoing: Input,
    incoming: Input,
    *,
    color: rgba = rgba(255, 128, 32),
    start: sec = 0,
    duration: sec = 0.8,
    easing: easing = Easing.InOut,
) -> Input:
    """
    Film burn: a warm glow blooms across the frame, whites it out at the cut,
    and leaves `incoming` behind as it fades — the light leak of a reel
    burning through at the end of a roll.

    The glow is a radial gradient ADDED over everything, drifting left to
    right; it is returned in case its layer has to move. The cut itself is
    hard, hidden under the glow's brightest frames.

        filmBurn(clipA, clipB, duration=1.0)
    """
    from videocode.input.shape.Rectangle import Rectangle

    glow = Rectangle(
        width=_constants.WORLD_WIDTH * 1.6,
        height=_constants.WORLD_HEIGHT * 1.6,
        fillColor=RadialGradient((rgba(255, 244, 220), 0), (color, 40), (rgba(color.r, color.g, color.b, 0), 100)),
        strokeColor=TRANSPARENT,
    ).blendMode(BlendMode.ADD).opacity(0)

    half = duration / 2
    for o, i in easing.rangeIdx(0.0, 255.0, half):
        glow.apply(_opacity(o), start=start + i * SINGLE_FRAME)
    for o, i in easing.rangeIdx(255.0, 0.0, half):
        glow.apply(_opacity(o), start=start + half + i * SINGLE_FRAME)
    drift = _constants.WORLD_WIDTH / 3
    for x, i in Easing.Linear.rangeIdx(-drift, drift, duration):
        glow.apply(_position(x, 0), start=start + i * SINGLE_FRAME)
    outgoing.apply(_hide(), start=start + half)
    incoming.apply(_show(), start=start + half)
    return glow


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
