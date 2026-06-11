#!/usr/bin/env python3

from videocode.shader.ishader import FragmentShader
from videocode.ty import degree, maybe, number, percent


class lightSweep(FragmentShader):
    """
    A bright band of light sweeping across an `Input`.

    The band travels across the `Input`'s own bounding box over the effect's
    `duration` (it fully enters on one side and exits on the other).

    - `width`: band thickness as a percentage (0-100) of the bounding box.
    - `intensity`: strength of the additive white highlight (0-1).
    - `angle`: band tilt in degrees — 0 is a vertical band sweeping
      left -> right; positive angles tilt it like an italic stroke.
    - `group`: inputs whose sweep shares a group id are swept as ONE area
      (the union of their bounding boxes), so the band travels continuously
      across all of them. Defaults to a fresh id per `lightSweep()` instance —
      applying one instance to a `Text`/`Group` broadcasts that instance to
      every member, which therefore sweep continuously as a whole. Pass an
      explicit id to synchronize sweeps across separate `apply` calls.

    Example: `shape.apply(lightSweep(), start=0, duration=1.5)`
    """

    _nextGroup = 0

    def __init__(
        self,
        width: percent = 20,
        intensity: number = 0.8,
        angle: degree = 20,
        group: maybe[int] = None,
    ):
        if group is None:
            # Auto ids are negative so they can never collide with explicit
            # (user-chosen, conventionally >= 0) group ids.
            lightSweep._nextGroup -= 1
            group = lightSweep._nextGroup
        self.width = width
        self.intensity = intensity
        self.angle = angle
        self.group = group
