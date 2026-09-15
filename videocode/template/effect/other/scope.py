#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from videocode.constants import *
from videocode.shader.fragmentShader.crop import crop as _crop
from videocode.shader.ishader import Effect, IShader
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def scope(
    *,
    ratio: number = 2.39,
    start: sec = 0,
    duration: sec = 0.7,
    easing: easing = Easing.Out,
) -> Effect:
    """
    Slide cinemascope bars in until the visible image is `ratio`:1 — the
    "this bit is the film" marker. `2.39` is anamorphic scope, `1.85` is
    flat widescreen, `1` is a square crop.

    The bars are an animated `crop` on the input's own box, so they close in
    on the MEDIA, not on the frame: a portrait capture floating in a wide
    frame gets bars sized to the capture. The crop persists afterwards —
    `scope(ratio=0)` or `unscope()` opens it back up.

        clip.apply(scope())
        clip.apply(scope(ratio=1.85, duration=1))
    """
    # The input's box already fills the frame in the common case, so measure
    # against the frame: what fraction of the height survives at `ratio`:1.
    keep = (SCREEN_WIDTH / ratio) / SCREEN_HEIGHT if ratio > 0 else 1.0
    bar = max(0.0, (1.0 - keep) / 2) * 100

    def _apply(_input: Input) -> Generator[IShader, Any, None]:
        for b, i in easing.rangeIdx(0.0, bar, duration):
            yield _crop(top=b, bottom=b).at(start=start + i * SINGLE_FRAME)

    return _apply


def unscope(
    *,
    ratio: number = 2.39,
    start: sec = 0,
    duration: sec = 0.7,
    easing: easing = Easing.Out,
) -> Effect:
    """Open the `scope(ratio=...)` bars back to the full frame."""
    keep = (SCREEN_WIDTH / ratio) / SCREEN_HEIGHT if ratio > 0 else 1.0
    bar = max(0.0, (1.0 - keep) / 2) * 100

    def _apply(_input: Input) -> Generator[IShader, Any, None]:
        for b, i in easing.rangeIdx(bar, 0.0, duration):
            yield _crop(top=b, bottom=b).at(start=start + i * SINGLE_FRAME)

    return _apply
