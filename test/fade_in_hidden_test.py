#!/usr/bin/env python3
"""
`fadeIn()` hides the element until the fade starts, unless its opacity was
already written — by the author, or by an earlier fade out.
"""
import sys

sys.path.insert(0, ".")

import videocode.serialize as serialize  # noqa: E402
from videocode.context import Context  # noqa: E402


def opacityAt15(scene: str) -> float:
    report = serialize.execSource(scene, "test/fade_in_hidden_scene.py")
    assert report["ok"], report
    return Context.stateAt(0, 15)["Opacity"]


HEAD = "from videocode import *\n"
# Frame 15 is before the fade, which starts at second 1.
# Nothing wrote the opacity: hidden until the fade.
assert opacityAt15(HEAD + "Square(side=1).fadeIn(start=1)\n") == 0
# The author dimmed it first: what they wrote stands.
assert opacityAt15(HEAD + "Square(side=1).opacity(128).fadeIn(start=1)\n") == 128
# Said outright, either way.
assert opacityAt15(HEAD + "Square(side=1).fadeIn(start=1, hidden=False)\n") == 255
assert opacityAt15(HEAD + "Square(side=1).opacity(128).fadeIn(start=1, hidden=True)\n") == 0
# Faded out, then in again: the fade out wrote the opacity, nothing is added.
assert opacityAt15(HEAD + "Square(side=1).fadeOut().fadeIn(start=1)\n") == 0
print("\033[32m✓\033[0m  fadeIn hides until it starts, unless the opacity was already written")
