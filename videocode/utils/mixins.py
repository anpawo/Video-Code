#!/usr/bin/env python3

from __future__ import annotations

from videocode.ty import rgba, sec, maybe, frame
from typing import Self
from videocode.utils.decorators import propagate
from videocode.utils.bezier import Easing, easing as _easing


class _hasFillColor:

    @propagate
    def fillColor() -> rgba: ...

    def fill(self, color: rgba, *, easing: _easing = Easing.InOut, start: sec = 0, duration: sec = 0.4, offset: maybe[frame] = None) -> Self:
        return self.ease("fillColor", color, easing=easing, start=start, duration=duration, offset=offset)  # type: ignore[attr-defined, return-value]


class _hasStrokeColor:

    @propagate
    def strokeColor() -> rgba: ...

    def stroke(self, color: rgba, *, easing: _easing = Easing.InOut, start: sec = 0, duration: sec = 0.4, offset: maybe[frame] = None) -> Self:
        return self.ease("strokeColor", color, easing=easing, start=start, duration=duration, offset=offset)  # type: ignore[attr-defined, return-value]


class _hasStrokeWidth:

    @propagate
    def strokeWidth() -> rgba: ...


class _hasFillStroke(_hasFillColor, _hasStrokeColor, _hasStrokeWidth): ...
