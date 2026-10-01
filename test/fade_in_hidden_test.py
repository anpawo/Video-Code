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
# Said outright: never hidden.
assert opacityAt15(HEAD + "Square(side=1).fadeIn(start=1, hidden=False)\n") == 255
# Faded out, then in again: the fade out wrote the opacity, nothing is added.
assert opacityAt15(HEAD + "Square(side=1).fadeOut().fadeIn(start=1)\n") == 0
# A waitFor() moves the element's clock to the fade: the hiding still starts
# where the element was made, not there — it stood opaque for the whole wait.
report = serialize.execSource(HEAD + "a = Square(side=1)\na.fadeOut(duration=1)\nb = Square(side=1)\nb.waitFor(a).fadeIn()\n", "test/fade_in_hidden_scene.py")
assert report["ok"], report
assert Context.stateAt(1, 15)["Opacity"] == 0, Context.stateAt(1, 15)
# A Text is a group: what the author wrote on it counts too. Hidden a second
# time at frame 0, the fade opened BEHIND the line above it and the editor said so.
for written in ('Text("Merci").opacity(0)', 'Text("Merci")', "Square(side=1).opacity(0)", "Square(side=1)"):
    report = serialize.execSource(HEAD + f"a = Square(side=1)\nwait(1)\nt = {written}\nt.waitFor(a).fadeIn()\n", "test/fade_in_hidden_scene.py")
    assert report["ok"], report
    assert Context.backdatedWrites() == [], (written, Context.backdatedWrites())
print("\033[32m✓\033[0m  fadeIn hides until it starts, unless the opacity was already written")
