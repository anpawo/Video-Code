#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
from abc import abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, Iterable
from videocode.constants import *

if TYPE_CHECKING:
    from videocode.shader.ishader import IShader
    from videocode.input.input import Input


class Metadata:
    def __init__(self, *, interface: bool = False) -> None:
        # --- Index
        """
        Index of the `Input`.

        Groups do not have an index (they are just python wrapper)
        """
        noRegister = Context._noRegister
        noHiding = Context._noHiding

        self.index: int = cast(int, None) if (interface or noRegister) else Context.getIndex()

        # --- Position ---
        self.position: v2[wnumber, wnumber] = v2(0, 0)

        # --- Align ---
        self.align: v2[wnumber, wnumber] = v2(0.5, 0.5)

        # --- Scale ---
        self.scale: v2[wnumber, wnumber] = v2(1, 1)

        # --- Rotation ---
        self.rotation: number = 0

        # --- Opacity ---
        self.opacity: number = 255

        # --- Hidden ---
        self.hidden: bool = False

        # --- ZIndex ---
        # Defaults to creation order (no ties unless explicitly set).
        self.zIndex: int = self.index if self.index is not None else 0

        # Bumped via Context.nextZOrderSeq() every time zIndex is explicitly
        # set. Ties in zIndex are broken by this: the most recently changed
        # one wins (renders on top), regardless of creation order.
        self.zOrderSeq: int = 0

        # --- Blend mode ---
        # Compositing mode index (see shader/vertexShader/blendMode.py):
        # 0=normal, 1=multiply, 2=screen, 3=add. Default is normal.
        self.blendMode: int = 0

        # --- Track matte / mask ---
        # Index of another Input whose alpha masks this one (see
        # shader/vertexShader/matte.py). None = no matte. Travels to C++ as a
        # plain int (Metadata.matteSource, -1 = none).
        self.matteSource: int | None = None

        # --- Adjustment layer ---
        # When True this input is never drawn on its own; its fragment effects
        # grade the flattened composite of everything below its zIndex (see
        # shader/vertexShader/adjustmentLayer.py and input/AdjustmentLayer.py).
        self.isAdjustmentLayer: bool = False

        if not interface and not noRegister:
            Context.metas.append(self)

        # --- Offset ---
        self.lastAffectedFrame: frame = Context.waitOffset
        """
        Last frame affected by a `Transformation` from the last applied `Transformation`

        Starts at waitOffset because any waits should consume all previous effects.
        """
        self.transformationOffset: frame = self.lastAffectedFrame
        """
        Increased by `lastAffectedFrame` when flushed.

        Also starts at Global.waitOffset
        """

        # --- Delay ---
        self.pendingStart: sec = 0
        """
        Keep start through setattr.
        """
        self.pendingDuration: sec = SINGLE_FRAME
        """
        Keep duration through setattr.
        """
        self.pendingOffset: maybe[frame] = None
        """
        Keep transformation offset through setattr.
        """

        # --- Callbacks ---
        # preCallbacks: called before a shader is applied. Signature: (shader, start, duration, offset) -> bool.
        #   - Mutate the shader's fields to rewrite its values (e.g. wrap a position modulo a tile size).
        #   - Return True to drop the shader entirely (it never reaches the stack).
        #   - Return False to let the (possibly mutated) shader through as normal.
        # postCallbacks: called after a shader is applied. Signature: (shader, start, duration, offset) -> None.
        self.preCallbacks: dict[type[IShader], list[Callable[..., bool]]] = {}
        self.postCallbacks: dict[type[IShader], list[Callable[..., None]]] = {}

    def __str__(self) -> str:
        s = "\n"
        for k, v in self.__dict__.items():
            s += f"\t\t{k}={v}\n"
        return s


class StackAction:

    @abstractmethod
    def __init__(self): ...

    def __str__(self) -> str:
        return str(vars(self))

    def jsonSerialization(self):
        return vars(self)


class Wait(StackAction):
    def __init__(self, startFrame: int, numberOfFrame: int, stop: list[str], line: int = 0):
        self.action = self.__class__.__name__
        self.start = startFrame
        self.n = numberOfFrame
        # Which ambient clocks pause during the gap (Clock values; [] = none).
        self.stop = stop
        # The line it was written on. A wait is where the scene's time actually
        # joins — everything before it has ended, everything after starts from
        # there — so the editor draws it across the timeline, and a gesture that
        # lengthens something knows what will move because of it.
        self.line = line


class Timestamp(StackAction):
    def __init__(self, name: str, time: int):
        self.action = self.__class__.__name__
        self.name = name
        self.time = time


class Context:
    """
    Context containing the `Metadata` of the `Scene`.
    """

    # stack[inputIdx][-1]            = {"type": str, "args": dict}          — Create
    # stack[inputIdx][frameIdx][key] = {"type": shaderType, **shaderArgs}   — Apply
    # "Args" shaders use key "Args:{argName}" to allow multiple per frame.
    stack: dict[int, dict] = {}

    # Where each input came from: (file, line, python class). A SIDE TABLE, never
    # part of `stack` — C++ hands `stack[i]["args"]` straight into shader parsing
    # and diffs the dicts to decide what to rebuild, so a new key there would
    # both travel somewhere it does not belong and defeat the incremental reload.
    origin: dict[int, tuple[str, int, str]] = {}

    # Wait and Timestamp actions; C++ consumes these separately.
    events: list[StackAction] = []

    # Index of the next `Input`
    inputCounter: int = 0

    # Last ever affected frame
    lastEverAffectedFrame: frame = 0

    # Wait creates an offset affecting the start of any transformation
    waitOffset: frame = 0

    # Clear color of the frame, normalized 0..1 RGB — set by assigning a
    # plain `rgba` to the script-global `BG` (resolved by serialize.py after
    # the scene runs; C++ reads this attribute like lastEverAffectedFrame).
    # None = the renderer's default dark gray.
    backgroundColor: tuple[float, float, float] | None = None

    # Monotonic counter for zIndex tiebreaks — see Metadata.zOrderSeq
    zOrderCounter: int = 0

    # Stack keys that are two names for one state — writing one on a frame
    # removes the other. See Context.apply().
    _EXCLUSIVE: dict[str, str] = {"Hide": "Show", "Show": "Hide"}

    # True while a Group is emitting toward its members.
    #
    # What reaches a member then is not an instruction someone wrote about that
    # member — it is the group's transform, worked out for that frame. A group
    # re-emits its whole window on every `apply`, so two chained animations look
    # from the outside like two statements fighting over the same key, when
    # `_rigidTimeline` has in fact already composed them per channel. Telling the
    # two apart is what keeps `contendedKeys()` from crying wolf on
    # `g.scaleTo(...).rotateBy(...)` — and what keeps it ABLE to speak up when a
    # member is written directly during a group's window, which is a real
    # conflict (council of 2026-08-26: warn, do not compose).
    deriving: bool = False

    # Every non-interface Metadata ever created — used to resolve relative
    # layer-order operations (bringToFront, sendToBack, bringForward, sendBackward).
    metas: list[Metadata] = []

    # When True, Input.__new__ skips index assignment and @inputCreation skips
    # Context.create().  Used by MergeGroup to build member geometry without
    # registering each member as a C++ input.
    _noRegister: bool = False

    # When True, Input@inputCreation skips the hiding until waitOffset.
    _noHiding: bool = False

    @staticmethod
    @contextmanager
    def noRegister():
        prev = Context._noRegister
        Context._noRegister = True
        try:
            yield
        finally:
            Context._noRegister = prev

    @staticmethod
    @contextmanager
    def noHiding():
        prev = Context._noHiding
        Context._noHiding = True
        try:
            yield
        finally:
            Context._noHiding = prev

    @staticmethod
    def getIndex() -> int:
        Context.inputCounter += 1
        return Context.inputCounter - 1

    @staticmethod
    def nextZOrderSeq() -> int:
        Context.zOrderCounter += 1
        return Context.zOrderCounter

    @staticmethod
    def maxZIndex() -> int:
        return max((m.zIndex for m in Context.metas if m.zIndex != BACKGROUND_Z_INDEX), default=0)

    @staticmethod
    def minZIndex() -> int:
        return min((m.zIndex for m in Context.metas if m.zIndex != BACKGROUND_Z_INDEX), default=0)

    @staticmethod
    def zIndexAbove(z: int) -> maybe[int]:
        """Smallest zIndex among all non-background inputs strictly greater than `z`, or None."""
        candidates = [m.zIndex for m in Context.metas if m.zIndex != BACKGROUND_Z_INDEX and m.zIndex > z]
        return min(candidates) if candidates else None

    @staticmethod
    def zIndexBelow(z: int) -> maybe[int]:
        """Largest zIndex among all non-background inputs strictly less than `z`, or None."""
        candidates = [m.zIndex for m in Context.metas if m.zIndex != BACKGROUND_Z_INDEX and m.zIndex < z]
        return max(candidates) if candidates else None

    @staticmethod
    def create(inputIndex: int, inputType: str, inputArgs: dict[str, Any]):
        Context.stack.setdefault(inputIndex, {})[-1] = {"type": inputType, "args": inputArgs}
        Context.origin[inputIndex] = Context._callSite()

    @staticmethod
    def _callSite() -> tuple[str, int, str]:
        """
        Where in the USER's file this input was made, and what class made it.

        `inputType` is the C++ factory key, so every shape in a scene comes back
        as "Polygon" and a `Text` arrives as one input per glyph — the stack
        cannot say what a person wrote. This walks out of the library to the
        first frame that is not ours, which is the right answer whether the call
        was written there directly or three levels down inside `Text.__init__`,
        and it is honest under `from videocode import *` by construction.

        The innermost library frame's `self` recovers the class the stack
        destroys: `Text`, `Square`, `Circle`.
        """
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep
        library = os.path.join(here, "videocode") + os.sep

        frame = sys._getframe(2)
        cls = ""
        # The last library function crossed on the way out — `moveBy`,
        # `scaleTo`, `fadeIn`. The stack knows which method a person called; the
        # shaders it produced do not, and the editor needs it to offer "remove
        # this" on the right call of a chain rather than on the whole line.
        func = ""
        while frame is not None:
            name = frame.f_code.co_filename
            if not name.startswith(library):
                Context.lastCallFunction = func
                return (name, frame.f_lineno, cls)
            if not frame.f_code.co_name.startswith("_") and frame.f_code.co_name not in (
                "apply", "broadcast", "noteStatement", "wrapper", "inner",
            ):
                func = frame.f_code.co_name
            # The OUTERMOST library frame's `self`, not the innermost: a
            # `Text` builds `Letter`s, and the letter is an implementation
            # detail of the word. Overwriting as the walk goes outward leaves
            # the last one standing, which is the class the author named.
            owner = frame.f_locals.get("self")
            if owner is not None:
                cls = type(owner).__name__
            frame = frame.f_back
        Context.lastCallFunction = func
        return ("", 0, cls)

    # One entry per apply() that reached the stack: which input, which line of
    # the person's file, which shader keys, and the frames it covers. A SIDE
    # TABLE like `origin` — the stack itself is handed to C++ and diffed, so
    # nothing that is only for the editor may live in it.
    statements: list[dict[str, Any]] = []

    # Filled by the last `_callSite()`: the library function the person called.
    lastCallFunction: str = ""

    @staticmethod
    def noteStatement(
        inputIndex: int, touched: dict[str, list[int]], offset: int = 0, cursor: int = 0
    ) -> None:
        """
        Record where a statement was written, and what it covers.

        The line is read here rather than per shader: the walk out of the library
        costs about 2 µs, an animation is hundreds of shaders, and every one of
        them came from the same line anyway.
        """
        file, line, _ = Context._callSite()
        Context.statements.append({
            "file": file,
            "line": line,
            "call": Context.lastCallFunction,
            "input": inputIndex,
            "keys": {name: (span[0], span[1]) for name, span in touched.items()},
            # An emission a Group worked out, rather than a line someone wrote.
            "derived": Context.deriving,
            "offset": offset,
            # Where the element's cursor stands once this statement is done —
            # which is what a statement written on the NEXT line would count its
            # `start` from. The editor needs it to write a `hide` at a chosen
            # moment: `hide(start=…)` is seconds after the cursor, and the
            # cursor is nowhere in the buffer.
            "cursor": cursor,
        })

    @staticmethod
    def contendedKeys() -> list[dict[str, Any]]:
        """
        Statements that claim the same CHANNEL, on the same input, over frames
        that overlap — the one case where the order the two lines were TYPED in
        decides what the video looks like.

        Two claims on one channel cannot both hold: the later call wins the
        frames they share. `moveTo(x=2)` against `moveTo(x=5)` over the same
        second is not a compromise between the two, and swapping the lines gives
        a different video.

        A channel is finer than a shader class — `Position:x`, `Args:fillColor` —
        because an effect claims only what it was given. Two effects on different
        channels COMPOSE, whatever their windows, and reporting those would be
        crying wolf on the very thing the claim model exists to allow.

        Four things are deliberately NOT reported, because they are how a scene
        is written rather than a mistake:

        - Different channels. x against y, `fillColor` against `strokeColor`.
        - A construction call. `position(x=-4)` covers the single instant it
          lands on; `moveTo(x=4, duration=1)` starting there is the animation
          reading its own starting value, not fighting it. Both statements must
          cover more than one frame.
        - A single frame in common. Two animations that meet end-to-start touch
          on the frame they hand over, and the later one is meant to win it.
        - Two emissions a GROUP worked out. A group re-emits its whole window on
          every `apply`, so `g.scaleTo(...).rotateBy(...)` looks from outside like
          two statements fighting — when `_rigidTimeline` has already composed
          them per channel. A member written by hand during a group's window is
          still reported: there the two really do disagree.

        Nothing here is sent to C++ and nothing is prevented — it is a reading
        of `statements`, which the editor already keeps.
        """
        # ── One emitter call is ONE statement ─────────────────────────────
        # `ease()`, and everything built on it — `over()`, `easeTogether`,
        # `fillIn` — writes a frame at a time, so a 47-frame ramp arrives here as
        # 47 statements one frame long. Counting those raw made the whole of
        # paint animation invisible: every span was a single frame, and a single
        # frame is rightly never contended. Two `over().fillColor` overlapping by
        # 15 frames reported nothing at all.
        #
        # Grouped by (input, file, line, call) — the same grouping the editor
        # already uses to draw one bar per call (see `serialize.sceneModel`).
        calls: dict[tuple[Any, ...], dict[str, list[int]]] = {}
        for st in Context.statements:
            spans = calls.setdefault((st["input"], st["file"], st["line"], st["call"], st.get("derived", False)), {})
            for key, (first, last) in st["keys"].items():
                held = spans.get(key)
                if held is None:
                    spans[key] = [first, last]
                else:
                    held[0] = min(held[0], first)
                    held[1] = max(held[1], last)

        byKey: dict[tuple[int, str], list[dict[str, Any]]] = {}
        for (inputIndex, file, line, call, derived), spans in calls.items():
            for key, (first, last) in spans.items():
                if last - first <= 1:
                    continue
                byKey.setdefault((inputIndex, key), []).append(
                    {"key": key, "input": inputIndex, "first": first, "last": last,
                     "file": file, "line": line, "call": call, "derived": derived}
                )

        found: list[dict[str, Any]] = []
        for spans in byKey.values():
            for i, a in enumerate(spans):
                for b in spans[i + 1:]:
                    # Two emissions a group worked out are not rivals: they are
                    # the same transform, composed per channel by `_rigidTimeline`
                    # before being sent. One derived and one written by hand IS a
                    # rival — that is the group-versus-member case, and it must
                    # still be said (council of 2026-08-26: warn, do not compose).
                    if a["derived"] and b["derived"]:
                        continue
                    shared = min(a["last"], b["last"]) - max(a["first"], b["first"])
                    if shared > 1:
                        found.append({"key": a["key"], "input": a["input"], "frames": shared,
                                      "from": max(a["first"], b["first"]), "a": a, "b": b})
        return found

    @staticmethod
    def apply(inputIndex: int, shaderName: str, shaderType: str, shaderArgs: dict[str, Any]):
        frameIdx = shaderArgs["start"]
        argName = shaderArgs.get("name") if shaderName == "Args" else None
        dictKey = f"Args:{argName}" if argName is not None else shaderName
        onFrame = Context.stack.setdefault(inputIndex, {}).setdefault(frameIdx, {})
        # One piece of state, two names. Left side by side on a frame, both
        # travelled to C++ and the dict's INSERTION order — the order the two
        # calls happened to be typed in — decided which one held. Dropping the
        # one being contradicted makes the frame single-valued, which is what
        # it already meant; the survivor is the same one C++ was picking.
        opposite = Context._EXCLUSIVE.get(dictKey)
        if opposite is not None:
            onFrame.pop(opposite, None)
        # A component this effect does not CLAIM is a hole, not a value — and the
        # frame already holds what belongs in it. Filling the hole from the entry
        # being replaced is what lets two effects share a frame: before this, the
        # second simply erased the first, whatever channel it had really changed.
        #
        # This settles the collision ON a frame. A frame that only one of them
        # covers has no neighbour to fill from, and its hole travels to C++, where
        # an absent component means "leave that channel alone" and the carry holds
        # the value — that is what settles it BETWEEN frames.
        held = onFrame.get(dictKey)
        if held is not None:
            heldArgs = held["args"]
            for name, value in shaderArgs.items():
                if value is None and heldArgs.get(name) is not None:
                    shaderArgs[name] = heldArgs[name]
        onFrame[dictKey] = {
            "type": shaderType,
            "args": shaderArgs,
        }


def wait(n: sec = 0, stop: Clock | Iterable[Clock] | None = None) -> None:
    """
    Wait for all animations to end, then leave `n` seconds where nothing new
    is scheduled. By default the world stays ALIVE during the gap — shader
    fills keep animating, videos keep playing; `stop` pauses selected
    ambient clocks for the span:

        wait(2)                        # gap, everything keeps living
        wait(2, stop=Clock.VIDEOS)     # gap, footage pauses, fills breathe
        wait(2, stop=[Clock.VIDEOS, Clock.PAINTS])
        freeze(2)                      # = wait(2, stop=<all clocks>)

    A paused clock RESUMES where it stopped (pause, not skip). Scheduled
    state (positions, colors, visibility) always simply holds — there is
    nothing to stop.
    """
    n = int(n * FRAMERATE)

    if stop is None:
        stopped: list[str] = []
    elif isinstance(stop, Clock):
        stopped = [stop.value]
    else:
        stopped = sorted(c.value for c in stop)

    # Python
    startFrame = max(Context.lastEverAffectedFrame, Context.waitOffset)
    Context.waitOffset = Context.lastEverAffectedFrame = startFrame + n

    Context.events.append(Wait(startFrame, n, stopped, Context._callSite()[1]))


def freeze(n: sec = 0) -> None:
    """
    A literal FREEZE-FRAME: `wait(n)` with every ambient clock stopped — the
    last rendered frame holds for `n` seconds (shader fills, videos and
    time-driven effects all pause, then resume where they stopped).
    """
    wait(n, stop=tuple(Clock))


def timestamp(name: str) -> None:
    Context.events.append(Timestamp(name, Context.lastEverAffectedFrame))
