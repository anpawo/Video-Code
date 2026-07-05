#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Literal
from videocode.constants import *
from videocode.shader.fragmentShader.crop import crop as _crop
from videocode.shader.vertexShader.hide import hide as _hide
from videocode.shader.vertexShader.opacity import opacity as _opacity
from videocode.shader.vertexShader.position import position as _position
from videocode.shader.vertexShader.show import show as _show
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input

type direction = Literal["left", "right", "top", "bottom"]

_DIR: dict[str, tuple[float, float]] = {"left": (-1, 0), "right": (1, 0), "top": (0, 1), "bottom": (0, -1)}
_OPPOSITE: dict[str, str] = {"left": "right", "right": "left", "top": "bottom", "bottom": "top"}

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
    direction: direction = "left",
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

        push(slide1, slide2, direction="left", duration=0.6)
    """
    dx, dy = _DIR[direction]
    ox, oy = _DIR[_OPPOSITE[direction]]

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
    direction: direction = "left",
    start: sec = 0,
    duration: sec = 0.5,
    easing: easing = Easing.InOut,
) -> None:
    """
    Wipe transition: a hard edge sweeps across revealing `incoming` from
    underneath `outgoing`, sweeping toward `direction`. Both inputs should
    already be positioned in the same spot (`incoming` sits behind/below
    `outgoing` — set zIndex if they aren't already stacked correctly).

        wipeBetween(sceneA, sceneB, direction="right", duration=0.5)
    """
    side = _OPPOSITE[direction]
    incoming.apply(_show()).apply(_crop(**{side: 100.0}), start=start)
    for p, i in easing.rangeIdx(100.0, 0.0, duration):
        incoming.apply(_crop(**{side: p}), start=start + i * SINGLE_FRAME)
    outgoing.apply(_hide(), start=start + duration)
