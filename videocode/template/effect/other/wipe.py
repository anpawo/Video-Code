#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any, Literal
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.fragmentShader.crop import crop as _crop
from videocode.shader.vertexShader.hide import hide as _hide
from videocode.shader.vertexShader.show import show as _show
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input

type direction = Literal["left", "right", "top", "bottom"]

# The wipe front enters from `direction`, so the side still hidden — the one
# whose crop percentage animates — is the opposite side.
_OPPOSITE: dict[str, str] = {"left": "right", "right": "left", "top": "bottom", "bottom": "top"}


def wipeIn(
    *,
    direction: direction = "left",
    start: sec = 0,
    duration: sec = 0.5,
    easing: easing = Easing.InOut,
) -> Effect:
    """
    Reveal the target with a directional wipe (animated `crop`): pixels appear
    starting from the `direction` side, sweeping across.

    The target is visible from `start` (a `show()` is emitted) but fully
    cropped on the first frame, so it can sit hidden before the effect:

        rect.hide().wait(1).apply(wipeIn())
        title.apply(wipeIn(direction="top", duration=0.8))
    """
    side = _OPPOSITE[direction]

    def _apply(_input: Input) -> Generator[IShader, Any, None]:
        yield _show().at(start=start)
        for p, i in easing.rangeIdx(100.0, 0.0, duration):
            yield _crop(**{side: p}).at(start=start + i * SINGLE_FRAME)

    return _apply


def wipeOut(
    *,
    direction: direction = "right",
    start: sec = 0,
    duration: sec = 0.5,
    easing: easing = Easing.InOut,
) -> Effect:
    """
    Hide the target with a directional wipe: pixels disappear sweeping toward
    the `direction` side, and the target stays hidden afterwards (`hide()` is
    emitted at the end).

        rect.apply(wipeOut())
        title.apply(wipeOut(direction="bottom"))
    """
    side = _OPPOSITE[direction]

    def _apply(_input: Input) -> Generator[IShader, Any, None]:
        for p, i in easing.rangeIdx(0.0, 100.0, duration):
            yield _crop(**{side: p}).at(start=start + i * SINGLE_FRAME)
        yield _hide().at(start=start + duration)

    return _apply
