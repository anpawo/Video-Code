#!/usr/bin/env python3

from videocode.transformation.Transformation import Transformation


class grayscale(Transformation):
    """
    `Grayscale` `Transformation`. Persistent defines if you want it to be shown on the following frames.
    """

    def __init__(self, *, persistent=True) -> None:
        self.persistent = persistent
