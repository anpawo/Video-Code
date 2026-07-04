#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.opacity import opacity as _opacity
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def typewriter(
    *,
    interval: sec = 0.06,
    fade: sec = 0.0,
    start: sec = 0,
) -> Effect:
    """
    Reveal a `Text`'s letters one by one, left to right — the classic
    typewriter entrance.

    - `interval`: delay between two consecutive letters.
    - `fade`: per-letter fade duration; 0 makes letters pop in instantly.

    Each `typewriter()` instance keeps its own letter counter: `Group.apply`
    dispatches the effect once per member in order, and every call advances
    the stagger by `interval`. (Spaces aren't letters, so cadence is uniform
    across words.)

        txt = Text("Hello world").opacity(0)
        txt.apply(typewriter())
        txt.apply(typewriter(interval=0.03, fade=0.1))
    """
    index = 0

    def _apply(_input: Input) -> Generator[IShader, Any, None]:
        nonlocal index
        at = start + index * interval
        index += 1

        yield _opacity(0).at(start=start)
        if fade > 0:
            for o, i in Easing.Out.rangeIdx(0.0, 255.0, fade):
                yield _opacity(o).at(start=at + i * SINGLE_FRAME)
        else:
            yield _opacity(255).at(start=at)

    return _apply
