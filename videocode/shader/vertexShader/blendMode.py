#!/usr/bin/env python3

from __future__ import annotations

from typing import Literal

from videocode.shader.ishader import *

# The compositing modes, matching the C++ pipeline index (BlendModes.hpp) and
# Metadata.blendMode. "normal" is the default src-alpha "over". Named distinctly
# from the `blendMode` class below so both can be imported without collision.
type blendModeName = Literal["normal", "multiply", "screen", "add"]

# String → pipeline index. Resolved here (Python) so C++ / the JSON stack only
# ever sees the int — see `getMetadataFromArgs` (case BlendMode reads "mode").
_MODES: dict[str, int] = {"normal": 0, "multiply": 1, "screen": 2, "add": 3}


class blendMode(VertexShader):
    """
    Set the compositing blend mode of an `Input` — how its pixels combine with
    whatever is already drawn behind it.

    - `"normal"`   : standard alpha blend (default)
    - `"multiply"` : darkens (source × destination)
    - `"screen"`   : lightens (inverse-multiply)
    - `"add"`      : linear dodge, clips toward white

    Overlay is intentionally unsupported — it requires reading the destination
    pixel in the fragment shader, which the fixed-function blend pipeline cannot
    express.
    """

    def __init__(self, mode: blendModeName):
        if mode not in _MODES:
            raise ValueError(f"Unknown blend mode {mode!r}; expected one of {list(_MODES)}.")
        # Store the resolved int, never the string: the JSON stack and the C++
        # side only ever deal with the pipeline index.
        self.mode: int = _MODES[mode]

    def autodestroy(self, i: Input) -> bool:
        return i.meta.blendMode == self.mode

    def modify(self, i: Input):
        i.meta.blendMode = self.mode
