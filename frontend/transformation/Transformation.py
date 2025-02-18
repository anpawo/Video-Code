#!/usr/bin/env python3

from __future__ import annotations
from typing import Self

import inspect

from frontend.Global import Arguments


class Transformation:
    """
    Represents a `Transformation`.

    .. code-block:: python
        def move() -> Transformation: ...
        def zoom() -> Transformation: ...
        def fadeIn() -> Transformation: ...
        def fadeOut() -> Transformation: ...
        def grayscale() -> Transformation: ...

    """

    def attributes(self) -> Arguments:
        return [v for _, v in vars(self).items()]
