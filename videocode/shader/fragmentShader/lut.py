#!/usr/bin/env python3

from __future__ import annotations

from videocode.shader.ishader import FragmentShader
from videocode.ty import unumber


class lut(FragmentShader):
    """
    Apply a `.cube` 3D color-lookup-table as a color grade to an `Input`.

    Standard Adobe/DaVinci `.cube` LUTs work: `rect.apply(lut("warm.cube"))`.

    - `filepath`: path to a `.cube` file, resolved relative to the working
      directory exactly like `Image`/`Video` (raw `cv::imread`-style path). The
      file is parsed and uploaded to the GPU ONCE, C++-side, then cached and
      reused every frame it is active (see LutAtlas.hpp + createLutResources()).
    - `intensity` (0-1): dissolves between the original color (`0`) and the
      fully-graded color (`1`) — same naming precedent as `glow`'s intensity.

    NOTE FOR FUTURE READERS: `filepath` is read DIRECTLY off the args dict
    C++-side (AInput::getActiveEffectsAtFrame -> ActiveEffect::strParam), NOT
    through the numeric push-constant array — a string can't ride in `pc.p[]`,
    so the usual "alphabetical param order" trap does not apply to it. But
    `intensity` DOES still go through the normal numeric path (it is the only
    numeric arg, so it lands at `p[0]`); the renderer appends the LUT size as
    `p[1]` itself.
    """

    def __init__(self, filepath: str, intensity: unumber = 1.0):
        self.filepath = filepath
        self.intensity = intensity
