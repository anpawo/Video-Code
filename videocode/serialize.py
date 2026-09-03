#!/usr/bin/env python3

from __future__ import annotations

import json
import os
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
    # The side table too. The editor runs a scene on every gesture, and
    # statements that outlive their run pile up in it — a hundred a frame for a
    # group — until an effect is attributed to a line that moved three edits ago.
    Context.statements = []

    # And the register of every input's metadata, with the counter that breaks
    # ties between equal z-indices.
    #
    # `Context.metas` is what `bringToFront()` and friends read to answer "what
    # is the highest layer in this scene". Left standing between runs it grew by
    # one entry per input per execution — the editor runs a scene on every
    # gesture — and, worse, it answered from scenes that no longer exist:
    # deleting the line that said `zIndex(50)` did not stop `maxZIndex()` from
    # replying 50, so the next `bringToFront()` jumped over a layer nobody could
    # see any more.
    Context.metas = []
    Context.zOrderCounter = 0

    # And the flag a Group raises while it emits toward its members — a run that
    # died mid-emission must not leave the next one marking everything derived.
    Context.deriving = False
    Context.derivingGroup = None

    # The three counters that live on classes rather than on Context, and were
    # forgotten here for exactly that reason. They are not cosmetic: a shader
    # that unions on an auto-assigned group id gets a DIFFERENT id on the second
    # bake of the same file, so the editor — one process, one bake per gesture —
    # renders the same scene two different ways, and every incremental reload
    # sees that input as changed. Measured on video.py: input 288 goes from
    # group -1 to group -2 with not a character of the scene touched.
    from videocode.input.interface.Group import Group as _Group
    from videocode.shader.fragmentShader.lightSweep import lightSweep as _lightSweep
    from videocode.shader.fragmentShader.glitch import glitch as _glitch
    from videocode.shader.fragmentShader.mathShader import mathShader as _mathShader

    _Group._serial = 0
    _lightSweep._nextGroup = 0
    _mathShader._nextGroup = 0
    # The fourth counter, and the only one that changes PIXELS rather than an
    # id: glitch derives its slice noise from the seed, so two bakes of one
    # unchanged scene rendered differently. The editor bakes on every gesture.
    _glitch._nextSeed = 0


def _oneLine(hit: dict) -> str:
    """The gutter has one line, not a paragraph — the paragraph stays on stderr."""
    a, b = hit["a"], hit["b"]
    return (
        f"{b['call']}() and {a['call']}() (line {a['line']}) both write {hit['key']} over "
        f"{hit['frames']} shared frames — the later call wins them."
    )


def _reportContendedKeys() -> list[dict]:
    """
    Say it out loud when two statements write the same key over the same frames.

    Printed rather than raised: the strict rule would refuse to render a scene
    that renders today, and a scene being written is broken most of the time —
    the editor runs this on every keystroke. On the 52 scenes of the repository
    it says nothing at all, which is the point: it is silent until the ambiguity
    is real.
    """
    out: list[dict] = []
    for hit in Context.contendedKeys():
        a, b = hit["a"], hit["b"]
        origin = Context.origin.get(hit["input"])
        who = f"the {origin[2]} from {os.path.basename(origin[0])}:{origin[1]}" if origin else f"input {hit['input']}"
        print(
            f"[videocode] {os.path.basename(a['file'])}:{a['line']} {a['call']}() and "
            f"{os.path.basename(b['file'])}:{b['line']} {b['call']}() both write {hit['key']} on "
            f"{who}, over {hit['frames']} frames from frame {hit['from']}.\n"
            f"            Two claims on one channel cannot both hold, so the later call WINS the "
            f"frames they share — swapping the two lines gives a different video. Separate them "
            f"with flush() or a start=, or write the one thing you mean. (Different channels — x "
            f"against y, fillColor against strokeColor — compose, and are never reported here.)",
            file=sys.stderr,
        )
        # `line` is what the code pane needs (LSP counts from zero); `sourceLine`
        # and `input` are what the timeline and the effect tree need, so that the
        # bar and the row carrying the fault are found by identity rather than by
        # comparing numbers that count from different places.
        out.append({"line": b["line"] - 1, "sourceLine": b["line"], "input": hit["input"],
                    "file": b["file"], "message": _oneLine(hit)})
    return out

def _reportBackdatedWrites() -> list[dict]:
    """
    Say it out loud when a line reaches back behind one already written.

    An animation reads where to start from the CURSOR, which is right as long as
    the lines are written in the order they play. A `start=` that opens before a
    line written above it starts from a value belonging to a moment that has not
    happened yet — and the same two lines the other way round give a different
    video. Printed rather than fixed: reading the base from the stack instead
    would need every line to have run first, which is a change of when the whole
    scene is baked.
    """
    out: list[dict] = []
    for hit in Context.backdatedWrites():
        a, b = hit["a"], hit["b"]
        print(
            f"[videocode] {os.path.basename(b['file'])}:{b['line']} {b['call']}() opens at frame "
            f"{b['first']}, behind {os.path.basename(a['file'])}:{a['line']} {a['call']}() which was "
            f"written above it and opens at frame {a['first']}. Both write {hit['key']}.\n"
            f"            An animation starts from where the element stands once every line above it "
            f"has been counted — so this one starts from a value that belongs to a LATER moment, and "
            f"writing the two lines the other way round gives a different video. Put them in the "
            f"order they play, or give the earlier one its own start= too.",
            file=sys.stderr,
        )
        # `line` is what the code pane needs (LSP counts from zero); `sourceLine`
        # and `input` are what the timeline and the effect tree need, so that the
        # bar and the row carrying the fault are found by identity rather than by
        # comparing numbers that count from different places.
        out.append({"line": b["line"] - 1, "sourceLine": b["line"], "input": hit["input"],
                    "file": b["file"], "message": _oneLine(hit)})
    return out

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
    _reportContendedKeys()
    _reportBackdatedWrites()


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

        # ── One row per STATEMENT ─────────────────────────────────────────
        # A row is a CALL, not a shader run.
        #
        # It used to be the other way round: runs of consecutive frames were
        # found on the stack and then attributed back to whichever statement
        # overlapped them most. That answered a different question — "what
        # changed, and who is to blame" — and it got the two most visible things
        # wrong.
        #
        # It started late. A rotation has not turned by anything on its first
        # frame, so no shader is written there, and `rotateBy(180, duration=1.2)`
        # was drawn beginning one frame after the `scaleTo(0.5, duration=1.2)`
        # written to happen with it. Two calls of the same length, on the same
        # line, starting at different times: a display saying something the
        # scene does not.
        #
        # And it could not tell a call's own length from its side effects: a
        # group re-emits position for as long as ANYTHING in it moves, so
        # `scaleTo` looked as long as the group's whole activity.
        #
        # Each `apply()` now records the frames it COVERS — before no-op shaders
        # are dropped — so the frames a call is answerable for are known without
        # looking at what survived. A group emits per frame, which is why the
        # window is the union of every statement sharing a line and a call.
        windows: dict[tuple[int, str], dict] = {}
        for statement in Context.statements:
            if statement["input"] != index or statement["line"] <= 0:
                continue
            if not statement["keys"]:
                continue

            first = min(span[0] for span in statement["keys"].values())
            # Exclusive on the stack, inclusive here: `__end = start + duration`
            # points at the frame after the last one carrying anything.
            last = max(span[1] for span in statement["keys"].values()) - 1
            if last < first:
                last = first

            at = (statement["line"], statement["call"])
            held = windows.get(at)
            if held is None:
                windows[at] = {
                    "name": statement["call"],
                    "call": statement["call"],
                    "line": statement["line"],
                    "start": first,
                    "end": last,
                    "kinds": sorted(statement["keys"]),
                }
                continue

            held["start"] = min(held["start"], first)
            held["end"] = max(held["end"], last)
            held["kinds"] = sorted(set(held["kinds"]) | set(statement["keys"]))

        effects = sorted(windows.values(), key=lambda e: (e["start"], e["name"]))

        # ── Where a new statement about this element could go ─────────────
        # The lines that already say something about it, in the order they ran,
        # each with the cursor left standing after it. To write `hide` at a
        # chosen moment the editor puts it after the last of these whose cursor
        # is not already past that moment, and counts `start` from there.
        # Consecutive entries on one line are one point: a group re-emits its
        # members every frame, which is a hundred statements from one line.
        points: list[dict[str, Any]] = []
        for statement in Context.statements:
            if statement["input"] != index or statement["line"] <= 0:
                continue
            if points and points[-1]["line"] == statement["line"]:
                points[-1]["call"] = statement["call"]
                points[-1]["cursor"] = statement["cursor"]
                continue
            points.append({
                "line": statement["line"],
                "call": statement["call"],
                "cursor": statement["cursor"],
            })

        # ── When it is actually on screen ─────────────────────────────────
        # NOT "the frames it has entries on". A typewriter writes
        # `opacity(0)` at frame 0 for every letter before ramping each one in,
        # so by key presence all eight glyphs start together and the stagger —
        # the whole point of the gesture — disappears. Visibility lives in the
        # VALUE, and the predicate is the renderer's own: not hidden, and
        # opacity not zero (src/core/Core.cpp).
        # A state, not a set of frames. What a key says holds until another key
        # says otherwise: a square that fades in at frame 1 and is hidden at
        # frame 45 is on screen for all of 1…44, and it has entries on none of
        # them. Counting only the frames carrying keys ended the clip at 11,
        # where the fade stopped writing.
        opacity = 255.0
        hidden = False
        firstSeen = -1
        lastSeen = total - 1
        wasVisible = False
        for frame in frames:
            for key, shader in entry[frame].items():
                args = shader.get("args", {})
                if "opacity" in args:
                    opacity = args["opacity"]
                # `hide()` carries no arguments — the KEY is the whole
                # statement, the way the renderer reads it. Asking for a
                # `hidden` value left every hidden element on the timeline until
                # the end of the scene, which is exactly the length nobody
                # wanted to see.
                if key == "Hide":
                    hidden = True
                elif key == "Show":
                    hidden = False
            nowVisible = not hidden and opacity != 0
            if nowVisible and firstSeen < 0:
                firstSeen = frame
            if wasVisible and not nowVisible:
                lastSeen = frame - 1
            elif nowVisible and not wasVisible:
                # On again — and on until something turns it off, which is what
                # the scene ending is.
                lastSeen = total - 1
            wasVisible = nowVisible

        # Never on screen at all: drawn where its keys are, rather than not at
        # all, because a clip you cannot see is still a clip you have to find.
        if firstSeen < 0:
            firstSeen = frames[0] if frames else 0

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
                "points": points,
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


def templateCatalogue() -> list[dict]:
    """
    Everything a scene can be given, by name: shapes, media, and the composite
    templates the library builds out of them.

    Discovered, like the effects, and for the same reason — a hand-written list
    is wrong the day someone adds a file. The rule for what belongs here is the
    one the language already draws: an `Input` subclass reachable by name from
    `from videocode import *` is something a person could have typed, and
    nothing else is offered.

    The group is read from where the class lives — a shape, a piece of media, or
    a template assembled from them — because that is the only division a person
    browsing them cares about, and it is already true in the tree.
    """
    import importlib
    import inspect
    import pkgutil

    import videocode

    import videocode.template.input as templates

    from videocode.input.input import Input

    groups = {
        "videocode.input.shape": "shape",
        "videocode.input.media": "media",
        "videocode.input.interface": "interface",
    }

    def described(value) -> str:
        # The first line of the docstring, when there is one. Never a
        # description written here: what the class says about itself is what the
        # person reading the code will see, and two of them would drift apart.
        # Its OWN docstring, never an inherited one: `inspect.getdoc` walks up
        # to the base class, so eleven different shapes all introduced
        # themselves as "An `Input` is a source that you want to add to the
        # timeline of the video" — a sentence that tells you nothing about which
        # one to pick. A class that says nothing about itself says nothing here.
        told = value.__dict__.get("__doc__") or ""
        return told.strip().split("\n")[0][:120]

    def parameters(value) -> list[dict]:
        try:
            return [p for p in _effectParameters(value.__init__) if p["name"] != "self"]
        except (TypeError, ValueError):
            return []

    def required(value) -> list[str]:
        # What has no default. `Shadow(shape=…)` is about another input and
        # cannot be conjured on its own; `Video(filepath=…)` needs a file. The
        # editor asks before it writes rather than writing a call that raises.
        return [p["name"] for p in parameters(value) if not p["optional"]]

    found: list[dict] = []
    seen: set[str] = set()

    # What `from videocode import *` already gives a scene: no import to write.
    for name, value in vars(videocode).items():
        if name.startswith("_") or not inspect.isclass(value):
            continue
        if not issubclass(value, Input) or value is Input or inspect.isabstract(value):
            continue

        where = getattr(value, "__module__", "")
        group = next((tag for prefix, tag in groups.items() if where.startswith(prefix)), "")
        if not group:
            continue

        seen.add(name)
        found.append({
            "name": name, "group": group, "module": "",
            "says": described(value), "params": parameters(value),
            "required": required(value),
        })

    # And the composite ones, which are NOT in the star import — `Arrow` lives
    # in videocode.template.input.Arrow, so the module travels with the name the
    # way it does for effects: a button that writes a call without its import
    # writes a scene that does not run.
    for module in pkgutil.walk_packages(templates.__path__, templates.__name__ + "."):
        try:
            loaded = importlib.import_module(module.name)
        except Exception:
            continue
        for name, value in vars(loaded).items():
            if name.startswith("_") or name in seen or not inspect.isclass(value):
                continue
            if value.__module__ != module.name:
                continue
            if not issubclass(value, Input) or inspect.isabstract(value):
                continue

            seen.add(name)
            found.append({
                "name": name, "group": "template", "module": module.name,
                "says": described(value), "params": parameters(value),
                "required": required(value),
            })

    found.sort(key=lambda t: (t["group"], t["name"]))
    return found


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
    What a default is CALLED, when the library gives it a name.

    `Easing.Out` for the curve behind it, `BLUE_C` for the colour: the editor
    shows and writes what a person would have typed, and an object's own repr is
    an address nobody can paste into a call. Found by identity in the namespaces
    that name them, so a new easing or a new colour needs no entry here.

    An empty string for anything else, which reads as "no default to show".
    """
    import videocode.constants as constants

    from videocode.utils.bezier import Easing

    if value is None:
        return "None"

    for name, candidate in vars(Easing).items():
        if not name.startswith("_") and candidate is value:
            return f"Easing.{name}"

    # Colours by VALUE, not by identity: a signature's `fillColor=rgba(77, 111,
    # 71, 255)` is the same green as `GREEN_E` without being the same object,
    # and the name is what a person would have typed.
    from videocode.color import rgba

    if isinstance(value, rgba):
        for name, candidate in vars(constants).items():
            if name.isupper() and isinstance(candidate, rgba) and candidate == value:
                return name

    for name, candidate in vars(constants).items():
        if not name.startswith("_") and candidate is value and name.isupper():
            return name
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

        # Whether the call can be made without it. NOT "the default came back
        # empty": a colour the library does not name has no spelling to show and
        # is still optional, and treating it as required made `Square` look like
        # something you cannot place without answering two questions.
        out.append({
            "name": name,
            "default": written,
            "kind": kind,
            "optional": parameter.default is not inspect.Parameter.empty,
        })

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
        # Collected as well as printed. These two ran on every keystroke in the
        # editor and spoke only to stderr, which the editor does not read — the
        # one mechanism built to say "swapping these two lines gives a different
        # video" reached nobody who was editing. `Editor::executeScene` copies
        # every key of this dict through to QML, so returning them is the whole
        # of the wiring.
        warnings = _reportContendedKeys() + _reportBackdatedWrites()
        warnings = [w for w in warnings if w["file"] == filepath]
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
        # JSON, like `scene` below, because the bridge to the editor stringifies
        # every value it is handed: a plain list arrived in QML as the TEXT
        # "[]", which is truthy and has no `.map`, so every single execution
        # raised a TypeError and the diagnostics were never assigned. The
        # warnings this collects — two lines writing the same channel over the
        # same frames — had therefore never once been shown to anyone.
        "warnings": json.dumps(warnings),
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
