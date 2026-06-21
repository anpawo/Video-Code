#!/usr/bin/env python3

from __future__ import annotations

import math


from videocode import *


class Plane(Group):
    def __init__(
        self,
        center=False,
        margin: wnumber = 2,
    ) -> None:
        transparent = 0.05
        self._margin = margin

        step = 1 / 3
        w = WORLD_WIDTH + 2 * margin
        h = WORLD_HEIGHT + 2 * margin
        # Background is 1 unit larger on each side so its edge never enters the
        # viewport even at full drift.
        bg = Rectangle(
            width=w + 2,
            height=h + 2,
            fillColor=BLUE_B,
            strokeColor=TRANSPARENT,
        )

        super().__init__(
            bg,
            *[
                VerticalLine(
                    length=h + 2,
                    strokeWidth=0.01,
                    rounded=False,
                    fillColor=WHITE | transparent,
                ).position(x=i, y=0, offset=0)
                for i in floatRange(w / -2, w / 2 + step, step)
            ],
            *[
                HorizontalLine(
                    length=w + 2,
                    strokeWidth=0.01,
                    rounded=False,
                    fillColor=WHITE | transparent,
                ).position(x=0, y=i, offset=0)
                for i in floatRange(-h / 2 - step, h / 2 + step, step)
            ],
            *([Dot().position(0, 0, offset=0)] if center else []),
        )

        # The grid (and its background rectangle) shouldn't be considered
        # part of the layer stack — sendToBack/bringToFront/etc. should treat
        # user shapes as the whole scene, not get pushed behind/in front of it.
        self.background()

    def drift(
        self,
        dx: wnumber = -0.5,
        dy: wnumber = 0.25,
        duration: maybe[sec] = None,
    ) -> Self:
        from videocode.shader.vertexShader.position import position as _position
        from videocode.template.effect.core.moveTo import moveTo as _moveTo

        tile = 1 / 3
        dur = Context.lastEverAffectedFrame * SINGLE_FRAME if duration is None else duration

        def register(member: Input) -> None:
            ox = member.meta.position.x
            oy = member.meta.position.y

            def wrap(s: _position, *_: Any) -> bool:
                s.x = ox + math.fmod(s.x - ox, tile)
                s.y = oy + math.fmod(s.y - oy, tile)
                return False

            member.meta.preCallbacks.setdefault(_position, []).append(wrap)
            member.apply(
                *_moveTo(
                    member,
                    x=ox + dx * dur * 0.5,
                    y=oy + dy * dur * 0.5,
                    easing=Easing.Linear,
                    duration=dur,
                ),
                offset=0,
            )

        self.broadcast(register)
        return self
