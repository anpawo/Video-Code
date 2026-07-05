#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any, Literal
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.hide import hide as _hide
from videocode.shader.vertexShader.opacity import opacity as _opacity
from videocode.shader.vertexShader.position import position as _position
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input

type direction = Literal["left", "right", "top", "bottom"]

_DIR: dict[str, tuple[float, float]] = {"left": (-1, 0), "right": (1, 0), "top": (0, 1), "bottom": (0, -1)}


def slideIn(
    *,
    direction: direction = "left",
    distance: wnumber = 1.0,
    start: sec = 0,
    duration: sec = 0.5,
    easing: easing = Easing.Out,
) -> Effect:
    """
    Slide the target in from `direction` (offset by `distance` world units)
    while fading in — the standard editor entrance.

    The current position is the DESTINATION; the effect starts offset from it.

        rect.position(0, 0).apply(slideIn(direction="bottom"))
        title.apply(slideIn(distance=2, easing=Easing.Back))
    """
    dx, dy = _DIR[direction]

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        dst = v2(*input.meta.position)
        src = v2(dst.x + dx * distance, dst.y + dy * distance)
        for p, i in easing.rangeIdx(src, dst, duration):
            yield _position(p.x, p.y).at(start=start + i * SINGLE_FRAME)
        for o, i in Easing.Out.rangeIdx(0.0, 255.0, max(duration * 0.6, SINGLE_FRAME * 2)):
            yield _opacity(o).at(start=start + i * SINGLE_FRAME)

    return _apply


def slideOut(
    *,
    direction: direction = "right",
    distance: wnumber = 1.0,
    start: sec = 0,
    duration: sec = 0.5,
    easing: easing = Easing.In,
) -> Effect:
    """
    Slide the target out toward `direction` while fading; ends hidden
    (a `hide()` is emitted so it doesn't pop back once the frames run out).

        rect.apply(slideOut())
        title.apply(slideOut(direction="top", distance=2))
    """
    dx, dy = _DIR[direction]

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        src = v2(*input.meta.position)
        dst = v2(src.x + dx * distance, src.y + dy * distance)
        for p, i in easing.rangeIdx(src, dst, duration):
            yield _position(p.x, p.y).at(start=start + i * SINGLE_FRAME)
        fadeStart = start + duration * 0.4
        for o, i in Easing.In.rangeIdx(255.0, 0.0, max(duration * 0.6, SINGLE_FRAME * 2)):
            yield _opacity(o).at(start=fadeStart + i * SINGLE_FRAME)
        yield _hide().at(start=start + duration)

    return _apply
