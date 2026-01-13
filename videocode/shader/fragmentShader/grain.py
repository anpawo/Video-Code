#!/usr/bin/env python3

from videocode.shader.ishader import FragmentShader
from videocode.ty import unumber


class grain(FragmentShader):
    """
    Grain is a filter simulates the texture of analog film.

    The amount should be >= 0 and <= 1.
    """

    def __init__(
        self,
        amount: unumber,
    ):
        self.amount = amount
