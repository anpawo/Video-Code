#!/usr/bin/env python3

from __future__ import annotations

import json
import sys


sys.path.append(".")


from videocode.context import *
from videocode import *


def _resetContext():
    Context.stack = {}
    Context.events = []
    Context.inputCounter = 0
    Context.lastEverAffectedFrame = 0
    Context.waitOffset = 0
    Context.backgroundColor = None
    # A previous hot-reload's BG must not leak into a script that removed it.
    globals().pop("BG", None)


def _applyBackground() -> None:
    """
    Resolve the scene's optional script-global `BG` — the scene's
    background, COLOR-ONLY (any `rgba`, gradients included — never an
    `Input`: animated backgrounds stay explicit, e.g. `Plane().drift()` at
    the end of the script):

        BG = WHITE                        # anywhere in the script
        BG = LinearGradient(RED, BLUE)

    - A plain `rgba` becomes the renderer's clear color
      (`Context.backgroundColor`, read by C++ like lastEverAffectedFrame) —
      zero extra draw cost. Alpha is ignored (transparent backgrounds come
      from `--generate out.mov/.webm` instead).
    - A gradient can't be a clear value (a Vulkan clear is one RGBA
      constant), so it becomes one static full-frame background `Rectangle`
      — visible from frame 0 (`noHiding`) and layered behind everything
      (`background(offset=0)`, exactly like `Plane`'s own backdrop).
    """
    bg = globals().get("BG")
    if bg is None:
        return

    if isinstance(bg, (LinearGradient, RadialGradient, ConicGradient)):
        with Context.noHiding():
            Rectangle(
                width=WORLD_WIDTH, height=WORLD_HEIGHT, fillColor=bg, strokeColor=TRANSPARENT
            ).background(offset=0)
    elif isinstance(bg, rgba):
        Context.backgroundColor = (bg.r / 255, bg.g / 255, bg.b / 255)
    else:
        raise TypeError(f"BG must be an rgba color or a gradient, got {type(bg).__name__}")


def execScene(filepath: str) -> None:
    """
    Execute the scene file and populate Context.stack.
    C++ reads the stack directly via pybind11 — no JSON serialization.
    """
    _resetContext()

    with open(filepath, "r") as file:
        content = file.read()

    global __name__
    __name__ = "Scene"
    code = compile(content, filepath, "exec")

    import os

    if os.environ.get("VC_PROFILE"):
        import cProfile, pstats, io

        pr = cProfile.Profile()
        pr.enable()
        exec(code, globals())
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
        ps.print_stats(30)
        print("[profile] Top 30 cumulative:\n" + s.getvalue(), flush=True)
    else:
        exec(code, globals())

    _applyBackground()


def serializeScene(filepath: str) -> str:
    """
    Serialiaze a file representing a `Scene`.
    """
    _resetContext()

    # Read the content of the file
    with open(filepath, "r") as file:
        content = file.read()

    # Exec the file representing the `Scene`. It will update the globals in `Global`.
    global __name__
    __name__ = "Scene"
    code = compile(content, filepath, "exec")
    exec(code, globals())

    _applyBackground()

    return json.dumps(
        {"stack": Context.stack, "events": [e.jsonSerialization() for e in Context.events]},
        default=lambda x: x.jsonSerialization(),
    )


if __name__ == "__main__":
    print(serializeScene("video.py"), file=sys.stderr)
