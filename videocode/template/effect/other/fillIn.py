#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator

from videocode.color import LinearGradient
from videocode.constants import *
from videocode.shader.ishader import GroupEffect, IShader
from videocode.utils.bezier import *

if TYPE_CHECKING:
    from videocode.input.input import Input


def _stopsOf(paint: rgba) -> list[tuple[rgba, float]]:
    """A paint as a stop list — a solid colour is a gradient that never changes."""
    return list(paint.stops) if isinstance(paint, LinearGradient) else [(paint, 0.0), (paint, 100.0)]


def _colorAt(paint: rgba, position: percent) -> rgba:
    """The colour a paint shows at `position`% — LinearGradient.colorAt, lent to solids."""
    return paint.colorAt(position) if isinstance(paint, LinearGradient) else paint


def fillIn(
    color: rgba,
    *,
    over: maybe[rgba] = None,
    reverse: bool = False,
    band: percent = 0,
    angle: maybe[degree] = None,
    duration: sec = 1.0,
    easing: easing = Easing.InOut,
) -> GroupEffect:
    """
    Wipe a new fill across a shape, sweeping a boundary from one side to the
    other. The shape stays fully visible — it is the COLOUR that travels::

        nbr.apply(fillIn(LinearGradient(BLUE_C, RED_B)))    # over its current fill
        title.apply(fillIn(GOLD, over=WHITE, band=10, duration=2))
        bar.apply(fillIn(RED_B, reverse=True))              # enters from the right

    Not to be confused with `wipeIn`, which crops: there the shape itself is
    revealed pixel by pixel, here it is already there and only repaints.

    The new fill is revealed IN PLACE: at every frame the swept part shows the
    colour the final fill has at that exact position, so a gradient does not
    slide or stretch under the boundary — it is uncovered, like paint under a
    receding sheet.

    - `color`: the fill to reveal. A solid colour or a gradient.
    - `over`: the fill being wiped away. Defaults to what the shape has now.
    - `reverse`: sweep right → left instead.
    - `band`: width of the soft edge, in % of the shape. 0 (the default) is a
      hard cut, which is what a wipe usually wants; raise it for a fade.
    - `angle`: the axis to sweep along, as in `LinearGradient` (0 = left →
      right, 90 = bottom → top). Defaults to the angle of whichever paint is a
      gradient — a wipe has to travel along the gradient's own axis, or the
      reveal would not line up.

    A `GroupEffect`: it receives the whole `Text`, not its letters. It then
    ASSIGNS `fillColor` frame by frame instead of emitting shaders, because
    assignment is what routes a gradient through `Text`'s per-letter slicing —
    hand a letter the whole gradient and every glyph repaints its own copy.

    Both ends are stated outright rather than left to zero-width stops: a stop
    pinned at 0% or 100% still colours the very edge of a gradient, so a
    leftover one repaints the first or last sliver of the shape on the first
    and last frames.
    """

    def _apply(input: Input) -> Generator[IShader, Any, None]:
        frm: rgba = over if over is not None else input.fillColor  # type: ignore[attr-defined]
        axis = angle if angle is not None else next((p.angle for p in (color, frm) if isinstance(p, LinearGradient)), 0)

        for edge in easing.range(0.0, 100.0, duration):
            if edge <= 0:
                input.fillColor = frm  # type: ignore[attr-defined]
            elif edge >= 100:
                input.fillColor = color  # type: ignore[attr-defined]
            else:
                # `lo` closes the revealed side, `hi` opens the one still to
                # come; they are the same point when band is 0, a hard cut.
                boundary = 100.0 - edge if reverse else edge
                lo = max(boundary - band, 0.0) if reverse else boundary
                hi = boundary if reverse else min(boundary + band, 100.0)
                first, second = (frm, color) if reverse else (color, frm)

                input.fillColor = LinearGradient(  # type: ignore[attr-defined]
                    *[(c, p) for c, p in _stopsOf(first) if p < lo],
                    (_colorAt(first, lo), lo),
                    (_colorAt(second, hi), hi),
                    *[(c, p) for c, p in _stopsOf(second) if p > hi],
                    angle=axis,
                )
            input.flush()

        # An Effect must hand back a generator of shaders; this one emits none —
        # it works by assigning `fillColor`, which is what routes the value
        # through the group's own distribution. `yield from ()` is what makes
        # the function a generator without a line of dead code.
        yield from ()

    return GroupEffect(_apply)
