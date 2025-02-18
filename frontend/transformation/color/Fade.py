#!/usr/bin/env python3

from typing import Optional, Tuple
from frontend.transformation.Transformation import *

from frontend.Constant import *


class fade(Transformation):
    def __init__(self, side: Optional[side] = None, opacity: Tuple[uint, uint] = (255, 0)) -> None:
        """
        `Fade` from `side`.

        Modify `opacity` for a `Fade In` or a `Fade out`.
        """
        self.side = side
        self.opacity = opacity
