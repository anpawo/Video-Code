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
    Context.origin = {}


def _applyBackground(scope: dict) -> None:
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
    bg = scope.get("BG")
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

    code = compile(content, filepath, "exec")

    # A FRESH namespace per run, seeded from this module's own.
    #
    # The scene used to execute into `globals()` — this module's dict — so every
    # name it bound survived into the next run, along with anything a helper
    # mutated. Delete a line, run again, and the name it defined was still
    # there: the editor showed a scene that `--generate` (a fresh process) would
    # not produce, and the drift grew with the session. Measured cost of the
    # fresh dict: none — 2.5 vs 2.6 ms on scene.py, 12.4 vs 12.7 on eg.py, 231.8
    # vs 230.0 on the stress scene, all inside run-to-run noise.
    #
    # Seeded from this module rather than empty because a scene is written
    # against what `videocode/serialize.py` has already imported; `__name__` is
    # "Scene" so a script guarded by `if __name__ == "__main__"` behaves the way
    # it did.
    scope = dict(globals())
    scope["__name__"] = "Scene"

    import os

    if os.environ.get("VC_PROFILE"):
        import cProfile, pstats, io

        pr = cProfile.Profile()
        pr.enable()
        exec(code, scope)
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
        ps.print_stats(30)
        print("[profile] Top 30 cumulative:\n" + s.getvalue(), flush=True)
    else:
        exec(code, scope)

    _applyBackground(scope)


def sceneModel() -> dict:
    """
    What the last run made, in the terms a timeline needs.

    The stack is baked PER FRAME — `moveBy` is a `Position` shader on every frame
    it covers — so an "effect" here is a contiguous run of frames sharing one
    shader key. That is not a summary: it is the same data the renderer reads,
    read the other way round.

    Nothing is invented. An element's label and line come from `Context.origin`
    (the call site), its kind from the class that made it, and its span from the
    frames it actually has entries on, extended to the end of the scene because
    an input that exists keeps existing until the scene ends.
    """
    # The cursor IS the count.
    #
    # `lastEverAffectedFrame` is exclusive: `__end = start + duration`, so it
    # points at the frame after the last one carrying anything. Adding one
    # counted it twice, and the timeline drew a scene one frame longer than the
    # video the renderer writes — 2.733 s of editor for a 2.700 s file.
    #
    # The floor is the scene that animates nothing: everything lands on frame 0
    # with no duration, the cursor never leaves 0, and the one frame there is to
    # see still has to be counted. Without it a static scene renders an empty
    # file, which is what the C++ side did.
    total = max(Context.lastEverAffectedFrame, 1)
    elements = []

    for index in sorted(Context.stack):
        entry = Context.stack[index]
        frames = sorted(f for f in entry if f != -1)

        # One run per shader key: walk the frames it appears on and cut wherever
        # the sequence breaks.
        runs: dict[str, list[list[int]]] = {}
        for frame in frames:
            for key in entry[frame]:
                spans = runs.setdefault(key, [])
                if spans and spans[-1][1] == frame - 1:
                    spans[-1][1] = frame
                else:
                    spans.append([frame, frame])

        effects = [
            {"name": key, "start": span[0], "end": span[1]}
            for key, spans in runs.items()
            for span in spans
        ]
        effects.sort(key=lambda e: (e["start"], e["name"]))

        # ── When it is actually on screen ─────────────────────────────────
        # NOT "the frames it has entries on". A typewriter writes
        # `opacity(0)` at frame 0 for every letter before ramping each one in,
        # so by key presence all eight glyphs start together and the stagger —
        # the whole point of the gesture — disappears. Visibility lives in the
        # VALUE, and the predicate is the renderer's own: not hidden, and
        # opacity not zero (src/core/Core.cpp).
        opacity = 255.0
        hidden = False
        visible = []
        for frame in frames:
            for shader in entry[frame].values():
                args = shader.get("args", {})
                if "opacity" in args:
                    opacity = args["opacity"]
                if "hidden" in args:
                    hidden = bool(args["hidden"])
            if not hidden and opacity != 0:
                visible.append(frame)

        # An input that is still on screen at its last key stays on screen: the
        # scene ends, it does not.
        firstSeen = visible[0] if visible else (frames[0] if frames else 0)
        lastSeen = total - 1 if (visible and visible[-1] == frames[-1]) else (
            visible[-1] if visible else total - 1
        )

        file, line, cls = Context.origin.get(index, ("", 0, ""))
        elements.append(
            {
                "index": index,
                "kind": cls or entry[-1]["type"],
                "file": file,
                "line": line,
                "first": firstSeen,
                "last": lastSeen,
                "effects": effects,
            }
        )

    # ── Where the scene's time joins ──────────────────────────────────────
    # A `wait()` is the one place the language lets time propagate: everything
    # before it has ended, everything after starts from there. The editor draws
    # them across the tracks, because "will this push what follows?" is answered
    # by whether there is one — not by a rule the timeline invented.
    waits = [
        {"start": event.start, "frames": event.n, "line": event.line}
        for event in Context.events
        if isinstance(event, Wait)
    ]

    return {"fps": FRAMERATE, "frames": total, "elements": elements, "waits": waits}


def effectCatalogue() -> list[dict]:
    """
    Every effect a scene can apply, by name, discovered rather than listed.

    A hand-written list is a list that is wrong the day someone adds a file —
    and the editor offering an effect the library does not have would be the
    worst kind of lie, since it writes it into your scene.
    """
    import importlib
    import inspect
    import pkgutil

    import videocode.template.effect as effects

    from videocode.input.input import Input

    found: dict[str, str] = {}
    signatures: dict[str, list[dict]] = {}
    forms: dict[str, str] = {}
    for module in pkgutil.walk_packages(effects.__path__, effects.__name__ + "."):
        try:
            loaded = importlib.import_module(module.name)
        except Exception:
            continue
        for name, value in vars(loaded).items():
            if inspect.isfunction(value) and value.__module__ == module.name and not name.startswith("_"):
                if name not in found:
                    found[name] = module.name
                    forms[name], signatures[name] = _effectForm(name, value, Input)

    # The module comes back with the name because effects are NOT part of
    # `from videocode import *` — `flash` lives in
    # videocode.template.effect.other.flash and has to be imported by name. An
    # editor that writes `flash()` without the import writes a scene that does
    # not run, which is a worse gift than no button at all.
    #
    # The parameters come with it for the same reason one step further on: an
    # editor that offers a field the effect does not take, or misses the one it
    # is really about, writes a call that fails. They are READ off the signature,
    # never listed here — a list beside the code is a list that is wrong the
    # first time a default changes.
    return [
        {
            "name": name,
            "module": where,
            "form": forms.get(name, "effect"),
            "params": signatures.get(name, []),
        }
        for name, where in sorted(found.items())
    ]


def _effectForm(name: str, fn, inputClass) -> tuple[str, list[dict]]:
    """
    How this effect is WRITTEN, and the fields that go with it.

    Two families live in `template/effect`, and they are not called the same way:

    - the core transformations — `moveBy`, `scaleTo`, `rotateTo` — are generator
      functions taking the target as their first argument, and `Input` wraps each
      one in a method. What a person writes is `square.scaleTo(x=2)`, so that is
      what the editor writes, with the METHOD's own fields (`factor`, not the
      internal `input`).
    - everything else is a factory returning an effect, applied with
      `square.apply(flash())`.

    Told apart by the signature rather than by a list of names: a new core
    transformation lands in the right family the day it is written.
    """
    import inspect

    if inspect.isgeneratorfunction(fn):
        method = getattr(inputClass, name, None)
        if method is not None and inspect.isfunction(method):
            # `self` is the element; the editor knows which one.
            return "method", [p for p in _effectParameters(method) if p["name"] != "self"]
        # No method to hide behind: the element is passed by hand, which is what
        # `Input` itself does with the star — the function yields shaders.
        return "generator", [p for p in _effectParameters(fn) if p["name"] != "input"]

    return "effect", _effectParameters(fn)


def inputSignature(className: str) -> list[dict]:
    """
    What the call that makes an input takes, so the editor can offer its fields.

    Same rule as the effect catalogue: read off the class, never listed here. A
    `Video` answers with `cuts`, `startFrame`, `endFrame`, `speedRamps`… — which
    is how "trim this clip" becomes "write `endFrame`" without the editor
    knowing anything about video in particular.

    The class is found by name among the inputs the scene language exposes, so
    what the editor can edit is exactly what a person could have typed.
    """
    import inspect

    import videocode

    target = getattr(videocode, className, None)
    if target is None or not inspect.isclass(target):
        return []

    try:
        return [p for p in _effectParameters(target.__init__) if p["name"] != "self"]
    except (TypeError, ValueError):
        return []


def _namedEasing(value) -> str:
    """
    `Easing.Out` for the object behind it, or an empty string for anything else.
    """
    from videocode.utils.bezier import Easing

    if value is None:
        return "None"

    for name, candidate in vars(Easing).items():
        if not name.startswith("_") and candidate is value:
            return f"Easing.{name}"
    return ""


def _effectParameters(fn) -> list[dict]:
    """
    An effect's keyword arguments, as the editor needs them: a name, the default
    written the way Python would write it, and enough of a kind to pick a field.

    `start` is left out on purpose. It is the one argument the editor does not
    ask for — you say when an effect happens by dropping it on the element, not
    by typing a number.
    """
    import inspect

    out: list[dict] = []
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        return out

    for name, parameter in signature.parameters.items():
        if name.startswith("_") or name == "start":
            continue
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue

        default = parameter.default
        if default is inspect.Parameter.empty:
            written = ""
        elif isinstance(default, bool):
            written = "True" if default else "False"
        elif isinstance(default, (int, float)):
            written = repr(default)
        elif isinstance(default, str):
            written = repr(default)
        else:
            # An easing is written in a scene as `Easing.Out`, and that spelling
            # is what has to come back: the object's own repr is an address, which
            # nobody can paste into a call. Found by identity in the namespace
            # that names them, so a new easing needs no entry anywhere here.
            written = _namedEasing(default)

        annotation = parameter.annotation
        kind = annotation if isinstance(annotation, str) else getattr(annotation, "__name__", "")

        out.append({"name": name, "default": written, "kind": kind})

    return out


def execSource(source: str, filepath: str) -> dict:
    """
    Execute a scene held in MEMORY, and report what it made.

    The editor's buffer is the scene; it reaches disk only when you save. So the
    thing to execute is the text, and `filepath` is passed only so tracebacks and
    line numbers point at the file a person is looking at — `compile()` records
    it, and the frame walk that gives a clip its provenance reads it back.

    Returns, rather than raising: a scene that fails is the normal state of a
    scene being written, and the editor has somewhere to show the failure.
    Nothing is left half-applied — `Context` is reset before the run, and on a
    failure the caller keeps whatever it had.
    """
    _resetContext()

    scope = dict(globals())
    scope["__name__"] = "Scene"

    try:
        code = compile(source, filepath, "exec")
        exec(code, scope)
        _applyBackground(scope)
    except SyntaxError as error:
        return {
            "ok": False,
            "line": (error.lineno or 1) - 1,
            "column": max((error.offset or 1) - 1, 0),
            "message": error.msg or "syntax error",
        }
    except BaseException as error:
        # The innermost frame that is still the USER's — a traceback through the
        # library is true and useless; the line they can act on is the last one
        # inside the file they are editing.
        line = 0
        tb = error.__traceback__
        while tb is not None:
            if tb.tb_frame.f_code.co_filename == filepath:
                line = tb.tb_lineno - 1
            tb = tb.tb_next
        return {
            "ok": False,
            "line": line,
            "column": 0,
            "message": f"{type(error).__name__}: {error}",
        }

    return {
        "ok": True,
        "inputs": len(Context.stack),
        "frames": max(Context.lastEverAffectedFrame, 1),
        "fps": FRAMERATE,
        "scene": json.dumps(sceneModel()),
    }


def serializeScene(filepath: str) -> str:
    """
    Serialiaze a file representing a `Scene`.
    """
    _resetContext()

    # Read the content of the file
    with open(filepath, "r") as file:
        content = file.read()

    # Same fresh namespace as execScene, for the same reason: one run must not
    # inherit the names of the last.
    code = compile(content, filepath, "exec")
    scope = dict(globals())
    scope["__name__"] = "Scene"
    exec(code, scope)

    _applyBackground(scope)

    return json.dumps(
        {"stack": Context.stack, "events": [e.jsonSerialization() for e in Context.events]},
        default=lambda x: x.jsonSerialization(),
    )


if __name__ == "__main__":
    print(serializeScene("video.py"), file=sys.stderr)
