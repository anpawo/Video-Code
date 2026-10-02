#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from videocode.constants import *
from videocode.shader.fragmentShader.crop import crop as _crop
from videocode.shader.ishader import Effect, IShader
from videocode.template.effect.ramp import HOLD_NONE, holdAfter as _hold
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def scope(
    *,
    ratio: number = 2.39,
    start: sec = 0,
    duration: sec = 0.7,
    hold: sec = HOLD_NONE,
    easing: easing = Easing.Out,
) -> Effect:
    """
    Slide cinemascope bars in until the visible image is `ratio`:1 — the
    "this bit is the film" marker. `2.39` is anamorphic scope, `1.85` is
    flat widescreen, `1` is a square crop.

    The bars are an animated `crop` on the input's own box, so they close in
    on the MEDIA, not on the frame: a portrait capture floating in a wide
    frame gets bars sized to the capture.

    The bars do NOT stay by themselves. A shader posed on a frame with the
    default one-frame duration stops applying on the next one, so the bars
    spring back open the instant the move ends: set `hold` to the number of
    seconds they should stay, which means "until whatever opens them again".
    A 0.2 s gap between a `scope` and its `unscope` was enough to show the
    full frame for six frames and then slam the bars back — a visible
    flicker. `hold` costs film length when it runs past everything else, so
    it is asked for rather than assumed — see `holdAfter`.

        clip.apply(scope())                        # le mouvement seul
        clip.apply(scope(duration=0.6, hold=1.4))  # ... et il tient 1,4 s
        clip.apply(scope(ratio=1.85, duration=1))
    """
    # The input's box already fills the frame in the common case, so measure
    # against the frame: what fraction of the height survives at `ratio`:1.
    keep = (SCREEN_WIDTH / ratio) / SCREEN_HEIGHT if ratio > 0 else 1.0
    bar = max(0.0, (1.0 - keep) / 2) * 100

    def _apply(_input: Input) -> Generator[IShader, Any, None]:
        for b, i in easing.rangeIdx(0.0, bar, duration):
            yield _crop(top=b, bottom=b).at(start=start + i * SINGLE_FRAME)
        yield from _hold(_crop(top=bar, bottom=bar), start, duration, hold)

    return _apply


def unscope(
    *,
    ratio: number = 2.39,
    start: sec = 0,
    duration: sec = 0.7,
    hold: sec = HOLD_NONE,
    easing: easing = Easing.Out,
) -> Effect:
    """
    Open the `scope(ratio=...)` bars back to the full frame, and keep them
    open for `hold` seconds — see `scope` for why the hold is needed.
    """
    keep = (SCREEN_WIDTH / ratio) / SCREEN_HEIGHT if ratio > 0 else 1.0
    bar = max(0.0, (1.0 - keep) / 2) * 100

    def _apply(_input: Input) -> Generator[IShader, Any, None]:
        for b, i in easing.rangeIdx(bar, 0.0, duration):
            yield _crop(top=b, bottom=b).at(start=start + i * SINGLE_FRAME)
        yield from _hold(_crop(top=0.0, bottom=0.0), start, duration, hold)

    return _apply
