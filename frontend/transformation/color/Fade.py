#!/usr/bin/env python3

from typing import Optional, Tuple
from frontend.transformation.Transformation import *

from frontend.Constant import *


class fade(Transformation):
    def __init__(self, side: Optional[side] = None, startOpacity: uint = 255, endOpacity: uint = 0) -> None:
        """
        `Fade` from `side`.

        Modify `opacity` for a `Fade in` or a `Fade out`.
        """
        self.side = side
        self.startOpacity = startOpacity
        self.endOpacity = endOpacity
