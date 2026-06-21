#!/usr/bin/env python3

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Protocol

from videocode.ty import rgba, wnumber, maybe, wnumber
from typing import Self
from videocode.utils.decorators import autoProp, propagate

if TYPE_CHECKING:
    from videocode.input.input import Input


class _hasFillColor:

    @propagate
    def fillColor() -> rgba: ...


class _hasStrokeColor:

    @propagate
    def strokeColor() -> rgba: ...


class _hasStrokeWidth:

    @propagate
    def strokeWidth() -> rgba: ...


class _hasFillStroke(_hasFillColor, _hasStrokeColor, _hasStrokeWidth): ...
