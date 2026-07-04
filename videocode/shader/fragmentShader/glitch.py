#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import maybe, number, percent


class glitch(FragmentShader):
    """
    Digital glitch: horizontal slices of the `Input` randomly shift sideways
    while the color channels split (chromatic aberration). Time-driven — the
    slice pattern re-rolls ~24 times over the effect's duration.

    - `amount`: peak displacement as a percentage (0-100) of the screen width.
    - `slices`: number of horizontal bands.
    - `seed`: randomization seed. Defaults to a fresh value per `glitch()`
      instance so simultaneous glitches don't move in lockstep; pass an
      explicit value for reproducible output.

    Example: `img.apply(glitch(), duration=0.5)`
    """

    _nextSeed = 0

    def __init__(
        self,
        amount: percent = 1.5,
        slices: number = 12,
        seed: maybe[number] = None,
    ):
        if seed is None:
            glitch._nextSeed += 1
            seed = glitch._nextSeed
        self.amount = amount
        self.slices = slices
        self.seed = seed
