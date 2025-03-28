#!/usr/bin/env python3

from __future__ import annotations
from videocode.Constant import *


class Transformation:
    """
    Represents a `Transformation`.

    .. code-block:: python
        def move() -> Transformation: ...
        def zoom() -> Transformation: ...
        def fade() -> Transformation: ...
        def grayscale() -> Transformation: ...

    """

    startTime: sec
    endTime: sec | None  # None for the last frame included.
