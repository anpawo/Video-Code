#!/usr/bin/env python3

from __future__ import annotations

import math

from typing import TYPE_CHECKING, Generator, Any
from videocode.constants import *
from videocode.shader.ishader import IShader, Effect
from videocode.shader.vertexShader.position import position as _position
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def shake(
    *,
    amplitude: wnumber = 0.08,
    frequency: number = 12,
    axis: Axis = Axis.X,
    decay: bool = True,
    start: sec = 0,
    duration: sec = 0.5,
) -> Effect:
    """
    Shake the target around its current position — the classic "error" /
    attention shake.

    - `amplitude`: peak displacement in world units.
    - `frequency`: oscillations per second.
    - `axis`: `Axis.X` (default, editor-style horizontal shake), `Axis.Y`, or
      `Axis.BOTH` (circular-ish rumble; y runs on a cosine so the motion orbits).
    - `decay`: dampen the shake to zero over `duration` (recommended);
      `False` keeps full amplitude until the end, then snaps back.

    The offsets are deterministic (pure sine), so applying one `shake()` to a
    `Group` moves every member identically — the group shakes rigidly.

        rect.apply(shake())
        card.apply(shake(amplitude=0.15, axis=Axis.BOTH, duration=0.8))
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        src = v2(*input.meta.position)
        n = max(int(duration * FRAMERATE), 2)
        for i in range(n):
            t = i / (n - 1)
            if i == n - 1:
                yield _position(src.x, src.y).at(start=start + i * SINGLE_FRAME)
                continue
            envelope = (1.0 - t) if decay else 1.0
            angle = 2 * math.pi * frequency * t * duration
            ox = amplitude * math.sin(angle) * envelope if axis in (Axis.X, Axis.BOTH) else 0.0
            oy = amplitude * math.cos(angle) * envelope if axis in (Axis.Y, Axis.BOTH) else 0.0
            if axis is Axis.Y:
                oy = amplitude * math.sin(angle) * envelope
            yield _position(src.x + ox, src.y + oy).at(start=start + i * SINGLE_FRAME)

    return _apply
