#!/usr/bin/env python3

from __future__ import annotations

import math
from copy import copy as _shallow_copy
from typing import Any
from typing_extensions import TypeVar
from videocode.input.input import *
from videocode.input.interface.Interface import Interface
from videocode.shader.ishader import Effect, GroupEffect

_GROUP_T = TypeVar("_GROUP_T", bound=Input, default=Input)


class _MemberBase:
    """
    A member as it stood when the group was formed.

    `width` and `height` are frozen here for the same reason the position is:
    the pivot is measured from them, and a pivot measured from LIVE members is a
    pivot that moves while it is being used. `Group.width` reads
    `inp.meta.position` of its members, so once a rotation has started moving
    them, the box the pivot is sampled from is the box the rotation has already
    produced — the transform derives its centre from its own result.

    Measured on `Group(Group(a, b), c).rotateBy(90)`: the outer pivot went from
    (0.25, 0) before the animation to (0.50, 0) after, and `_emitRigid` asks for
    it on every emission.
    """

    #: The pivot of a MEMBER GROUP, or None for a leaf.
    #:
    #: A group is not AT its `meta.position`: that field is a displacement it
    #: adds to members it holds around its own pivot, so zero means "wherever
    #: they already are", not the origin. Reading it as a location made a
    #: parent turn a point its child's content was not at, and the formation
    #: came apart — `Group(Group(a, b), c).rotateBy(90)` left the squares
    #: 1 / 0.707 / 1.581 apart when they had started 1 / 1 / 2.
    #:
    #: So the base position of a member group is its pivot plus that
    #: displacement, and `_emitRigid` hands it back the displacement that lands
    #: the pivot where the parent wants it.
    pivot: maybe[v2]

    def __init__(self, member: Input) -> None:
        meta = member.meta
        self.pivot = member._pivot() if isinstance(member, Group) else None
        self.position = v2(*meta.position) if self.pivot is None else self.pivot + v2(*meta.position)
        self.rotation = meta.rotation
        self.scale = v2(*meta.scale)
        self.width = member.width
        self.height = member.height


class Group(Interface, Generic[_GROUP_T]):
    # fmt: off
    """
    A `Group` contains many inputs. Position, rotation and scale transforms
    applied to the group use orbital rigid-body math — members pivot together
    around the group's `align` anchor — while other shaders (color, opacity,
    etc.) broadcast as-is to all members.

    Also used to create bigger things that link many Inputs.
    You create a class that inherits from `Group`, setup your things and then super().__init__().

    Member states are frozen at the moment the group is created. Call
    `_regroup()` to re-snapshot after members have been individually repositioned.
    """
    # fmt: on

    def __init__(self, *inputs: Input):
        self.inputs: list[_GROUP_T] = cast(list[_GROUP_T], list(inputs))
        self._snapshot()

    # ------------------------------------------------------------------
    # Snapshot / pivot helpers

    def _snapshot(self) -> None:
        """Snapshot current member position/rotation/scale as the rigid-body base."""
        self._memberBases: list[tuple[Input, _MemberBase]] = [(m, _MemberBase(m)) for m in self.inputs]
        # Per-frame rigid state recorded during the current time window, keyed by
        # relative frame (round(start * FRAMERATE)). It is what lets concurrent
        # chained rigid animations — `g.rotateBy(...).scaleTo(...)` — combine:
        # a member's position at a frame depends on the group's position AND
        # rotation AND scale at that frame, and the passes are written one after
        # another while the frames they cover overlap.
        #
        # Nothing is emitted while a pass runs. The whole timeline is emitted
        # once the call is over, because a pass can change frames an earlier pass
        # already answered for: `rotateBy(180, duration=1.5)` writes 45 frames of
        # orbit at scale 1, then `scaleTo(0.5, duration=0.5)` halves the group for
        # every frame from its 15th onwards — including the 30 the rotation had
        # already emitted. Emitting as we went left those 30 on the old orbit, so
        # the members shrank for half a second and then jumped back out to twice
        # the radius in one frame.
        self._rigidTimeline: dict[int, dict[str, Any]] = {}
        # What the last emission wrote, so an identical repeat costs nothing.
        self._rigidWritten: tuple = ()

    def _regroup(self) -> None:
        """Re-snapshot member bases from their current meta (call after layout changes)."""
        self._snapshot()

    #: The channels a group's rigid state is made of — one per independent
    #: number, exactly like a leaf's. `pos` and `scl` carry two axes each and an
    #: effect may claim one without the other, and `align` is here because it
    #: decides the PIVOT: a pivot is what every emission was computed from, so a
    #: later `align` must not reach back and change frames already written.
    _RIGID_CHANNELS = ("pos.x", "pos.y", "rot", "scl.x", "scl.y", "align.x", "align.y")

    def _rigidDefaults(self) -> dict[str, Any]:
        """Where each channel stands when the timeline says nothing about it."""
        return {
            "pos.x": self.meta.position.x, "pos.y": self.meta.position.y,
            "rot": self.meta.rotation,
            "scl.x": self.meta.scale.x, "scl.y": self.meta.scale.y,
            "align.x": self.meta.align.x, "align.y": self.meta.align.y,
        }

    @staticmethod
    def _assemble(channels: dict[str, Any]) -> dict[str, Any]:
        """Channels back into the shape `_emitRigid` reads."""
        return {
            "pos": v2(channels["pos.x"], channels["pos.y"]),
            "rot": channels["rot"],
            "scl": v2(channels["scl.x"], channels["scl.y"]),
            "align": v2(channels["align.x"], channels["align.y"]),
        }

    def _pivot(self, align: maybe[v2] = None) -> v2:
        """
        Pivot point in member-base space, determined by the group's alignment.

        Default align (0.5, 0.5) = center of the group's bounding box.
        This is the point that stays fixed when the group is rotated or scaled.

        `align` is the alignment for the frame being emitted, which is not always
        the group's current one — see `_RIGID_CHANNELS`.
        """
        if not self._memberBases:
            return v2(0.0, 0.0)
        ax, ay = align if align is not None else self.meta.align
        # Frozen extents, not live ones — see `_MemberBase`.
        lefts = [base.position.x - base.width / 2 for _, base in self._memberBases]
        rights = [base.position.x + base.width / 2 for _, base in self._memberBases]
        bots = [base.position.y - base.height / 2 for _, base in self._memberBases]
        tops = [base.position.y + base.height / 2 for _, base in self._memberBases]
        return v2(
            min(lefts) + ax * (max(rights) - min(lefts)),
            min(bots) + ay * (max(tops) - min(bots)),
        )

    # ------------------------------------------------------------------
    # Rigid-body emission

    def _stateAt(self, at: int) -> dict[str, Any]:
        """
        The group's position, rotation and scale at a frame.

        Each component is the last value it was given at or before that frame;
        before its first, the value the animation started from; and with nothing
        recorded at all, whatever the group's meta says.
        """
        channels = self._rigidDefaults()
        seen: set[str] = set()

        for f in sorted(self._rigidTimeline):
            rec = self._rigidTimeline[f]
            for key in Group._RIGID_CHANNELS:
                if key not in rec:
                    continue
                # Before its first record, a channel is whatever that first
                # record says: an animation starts from where the group already
                # was.
                if f > at and key in seen:
                    continue
                channels[key] = rec[key]
                seen.add(key)

        return Group._assemble(channels)

    def _emitRigid(
        self,
        start: sec,
        duration: sec,
        offset: maybe[frame],
        *,
        pos: bool = False,
        rot: bool = False,
        scl: bool = False,
        state: maybe[dict[str, Any]] = None,
    ) -> None:
        """
        Emit concrete position/rotation/scale shaders to each member, applying the
        group transform on top of each member's frozen base.

        `state` is the transform to use; without one the group's state at that
        frame is worked out from the timeline, which is what a caller outside the
        rigid passes — `Text.alignLetters` — wants.
        """
        if state is None:
            state = self._stateAt(round(start * FRAMERATE))
        if not self._memberBases:
            return

        gx, gy = state["pos"]
        grot_deg = state["rot"]
        gscale = state["scl"]

        C = self._pivot(state.get("align"))
        # C++ renders a positive degree as a clockwise spin on screen (the
        # rotation matrix is applied in pixel space, which is Y-flipped vs
        # world space) — the orbit must turn the same way or members shear
        # apart from their own spin.
        rad = math.radians(-grot_deg)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)

        for m, base in self._memberBases:
            shaders: list[IShader] = []

            if pos or scl:
                # Member offsets scale with the group (rigid scaling) and
                # rotate with it — a scale change moves off-pivot members too.
                rx = (base.position.x - C.x) * gscale.x
                ry = (base.position.y - C.y) * gscale.y
                wx = rx * cos_r - ry * sin_r + C.x + gx
                wy = rx * sin_r + ry * cos_r + C.y + gy
                # A member group reads a position as a displacement from its own
                # pivot — see `_MemberBase.pivot`.
                if base.pivot is None:
                    shaders.append(position(wx, wy))
                else:
                    shaders.append(position(wx - base.pivot.x, wy - base.pivot.y))

            if rot:
                shaders.append(rotation(base.rotation + grot_deg))

            if scl:
                shaders.append(scale(*(base.scale + gscale - v2(1.0, 1.0))))

            if shaders:
                # Marked as the group's own working-out, not as a line about this
                # member — see `Context.deriving`.
                wasDeriving = Context.deriving
                Context.deriving = True
                try:
                    m.apply(*shaders, start=start, duration=duration, offset=offset)
                finally:
                    Context.deriving = wasDeriving

    # ------------------------------------------------------------------
    # Interface

    def __iter__(self):
        for i in self.inputs:
            yield i

    def broadcast(self, func: Callable[[Input], Any]):
        for child in self.inputs:
            child.broadcast(func)

    def apply(self, *shaders: IShader | Effect | GroupEffect, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self:
        rigid = False
        for s in shaders:
            if isinstance(s, GroupEffect):
                # Group-scoped effect: gets the group itself. What it does only
                # means something across the members — a fill sweeping a Text
                # travels over the WORD, and a letter has no idea where it sits
                # in one. e.g. g.apply(fillIn(GOLD))
                self.apply(*s(self), start=start, duration=duration, offset=offset)
                continue

            if not isinstance(s, IShader):
                # Member-aware effect: Group dispatches it per-child, letting the
                # effect read each member's own state (scale, fillColor, …).
                # e.g. g.apply(highlight(color=YELLOW))
                for child in self.inputs:
                    child.apply(*s(child), start=start, duration=duration, offset=offset)
                continue

            # Keep group.meta current even though groups never push to C++.
            # Subclasses and external code read group.meta.* directly —
            # e.g. Text.alignLetters reads self.meta.align.x, or user code
            # inspects text.meta.position to query the group's current logical state.
            # Groups are otherwise stateless — children own the rendering state.
            # Read before `modify` moves it: an `align` that lands mid-window
            # needs to put the alignment it REPLACES on the timeline, or the
            # frames before it would be repainted with the new pivot.
            previousAlign = v2(*self.meta.align)
            if isinstance(s, VertexShader):
                _shallow_copy(s).modify(self)

            k = s._rigidKind
            if k:
                # Resolve the shader's own timing (.at(start=t) per animation frame)
                # before recording — each frame in a moveTo animation carries its own t.
                ts, td, to = s.resolve(start, duration, offset)
                rec = self._rigidTimeline.setdefault(round(ts * FRAMERATE), {})
                rec["t"] = (ts, td, to)
                # Only the components the shader CLAIMED, for the same reason a
                # leaf records only those: `g.moveTo(x=2)` followed by
                # `g.moveBy(y=3, start=0.5)` used to make x jump to its
                # destination the instant the y animation began writing —
                # the bug of the leaves, one level up.
                claimsX = getattr(s, "x", None) is not None
                claimsY = getattr(s, "y", None) is not None
                if k == 1:
                    if claimsX:
                        rec["pos.x"] = self.meta.position.x
                    if claimsY:
                        rec["pos.y"] = self.meta.position.y
                elif k == 2:
                    rec["rot"] = self.meta.rotation
                else:
                    if claimsX:
                        rec["scl.x"] = self.meta.scale.x
                    if claimsY:
                        rec["scl.y"] = self.meta.scale.y
                rigid = True
            else:
                # `align` is not a rigid transform — it broadcasts to the members
                # like any other shader, and that stays. But it ALSO moves the
                # group's pivot, and a pivot is what every emission was computed
                # from: applied between two rotations, it used to reach back and
                # rewrite frames that had already been written. Recorded on the
                # timeline, each frame keeps the pivot it was emitted with.
                #
                # Only while a timeline exists — a lone `align` on an unanimated
                # group has nothing to reach back into, and should stay the plain
                # broadcast it has always been.
                if isinstance(s, align) and self._rigidTimeline:
                    ts, td, to = s.resolve(start, duration, offset)
                    written = sorted(self._rigidTimeline)

                    # The alignment this one REPLACES belongs on the timeline
                    # first. The fold carries a channel backward from its first
                    # record — that is how an animation starts from where the
                    # group already was — so without this, an `align` written at
                    # frame 15 would hand its pivot to frames 0 through 14 as
                    # well, which is the retroactive rewrite being fixed.
                    if not any(k.startswith("align.") for f in written for k in self._rigidTimeline[f]):
                        opening = self._rigidTimeline[written[0]]
                        opening.setdefault("align.x", previousAlign.x)
                        opening.setdefault("align.y", previousAlign.y)

                    rec = self._rigidTimeline.setdefault(round(ts * FRAMERATE), {})
                    rec.setdefault("t", (ts, td, to))
                    if s.x is not None:
                        rec["align.x"] = float(s.x)
                    if s.y is not None:
                        rec["align.y"] = float(s.y)
                    rigid = True
                # All other shaders (color, opacity, args, translate, hide, …) broadcast
                # as-is to every member. i.apply() makes its own shallow copy for
                # VertexShaders before calling modify(), so passing s directly is safe.
                for i in self.inputs:
                    i.apply(s, start=start, duration=duration, offset=offset)

        if rigid:
            self._emitTimeline()

        return self

    def _emitTimeline(self) -> None:
        """
        Write every frame the timeline knows about, with the group's state AT that
        frame — the last value each component was given at or before it.

        Carried FORWARD because a transform holds until the next one: the scale a
        half-second animation lands on is the scale of every frame after it, and
        the members' orbit has to keep using it. Carried BACKWARD from the first
        record for frames an animation has not reached yet, since an animation
        starts from the value the group already had.

        Re-emitting is safe by construction: the stack keys a frame's entry by
        shader name, so writing frame 30's position twice replaces it rather than
        stacking two.
        """
        if not self._rigidTimeline:
            return

        frames = sorted(self._rigidTimeline)

        def firstOf(key: str, fallback: Any) -> Any:
            for f in frames:
                if key in self._rigidTimeline[f]:
                    return self._rigidTimeline[f][key]
            return fallback

        defaults = self._rigidDefaults()
        channels = {key: firstOf(key, defaults[key]) for key in Group._RIGID_CHANNELS}

        # Walk it once to know what would be written, and say nothing if that is
        # what was written last time.
        #
        # A group's `apply` runs far more often than a scene has animations — a
        # Text dispatches one per letter, 42 calls for two transforms — and
        # rewriting the whole window on each of them turned a two-transform Text
        # from 9 ms into 140. Skipping an IDENTICAL repeat is safe in a way that
        # skipping individual frames is not: a member's `autodestroy` drops a
        # shader that matches the member's current meta, so the meta trajectory
        # has to stay exactly what it would have been. A repeat re-walks the same
        # values in the same order and ends where it started; dropping it changes
        # nothing at all.
        plan: list[tuple[int, dict[str, Any], bool, bool]] = []
        for f in frames:
            rec = self._rigidTimeline[f]
            for key in Group._RIGID_CHANNELS:
                if key in rec:
                    channels[key] = rec[key]
            plan.append((f, Group._assemble(channels), "rot" in rec, "scl.x" in rec or "scl.y" in rec))

        signature = tuple(
            (f, float(st["pos"].x), float(st["pos"].y), float(st["rot"]),
             float(st["scl"].x), float(st["scl"].y),
             float(st["align"].x), float(st["align"].y), r, sc)
            for f, st, r, sc in plan
        )
        if signature == self._rigidWritten:
            return
        self._rigidWritten = signature

        for f, st, withRot, withScl in plan:
            ts, td, to = self._rigidTimeline[f]["t"]
            # Position is emitted for every frame — it is the one thing that
            # depends on all three — while rotation and scale are only written
            # where they actually change.
            self._emitRigid(ts, td, to, pos=True, rot=withRot, scl=withScl, state=st)

    # Advancing the time window (flush / wait / waitTo / waitFor) invalidates the
    # rigid timeline: its keys are frames relative to the members' transformation
    # offset, so a new window would collide with (and wrongly reuse) old entries.

    def flush(self) -> Self:
        self._rigidTimeline.clear()
        self._rigidWritten = ()
        return super().flush()

    def waitTo(self, n: frame) -> Self:
        self._rigidTimeline.clear()
        self._rigidWritten = ()
        return super().waitTo(n)

    def wait(self, n: sec) -> Self:
        self._rigidTimeline.clear()
        self._rigidWritten = ()
        return super().wait(n)

    def waitFor(self, i: Input) -> Self:
        self._rigidTimeline.clear()
        self._rigidWritten = ()
        return super().waitFor(i)

    def waitForOthers(self) -> Self:
        """Advance this group to the latest `lastAffectedFrame` among all members."""
        frames: list[int] = []

        def collect(i: Input) -> None:
            if isinstance(i, Interface):
                i.broadcast(collect)
            else:
                frames.append(i.meta.lastAffectedFrame)

        self.broadcast(collect)
        if not frames:
            return self
        return self.waitTo(max(frames))

    @staticmethod
    def _anchorOf(inp: Input) -> v2:
        """Where an input's content sits — for a group, not its `meta.position`."""
        p = v2(inp.meta.position.x or 0, inp.meta.position.y or 0)
        return p + inp._pivot() if isinstance(inp, Group) else p

    @property
    def width(self) -> wnumber:
        if not self.inputs:
            return 0
        anchors = [Group._anchorOf(inp).x for inp in self.inputs]
        rights = [a + inp.width / 2 for a, inp in zip(anchors, self.inputs)]
        lefts = [a - inp.width / 2 for a, inp in zip(anchors, self.inputs)]
        return max(rights) - min(lefts)

    @property
    def height(self) -> wnumber:
        if not self.inputs:
            return 0
        anchors = [Group._anchorOf(inp).y for inp in self.inputs]
        tops = [a + inp.height / 2 for a, inp in zip(anchors, self.inputs)]
        bots = [a - inp.height / 2 for a, inp in zip(anchors, self.inputs)]
        return max(tops) - min(bots)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}"

    def __repr__(self) -> str:
        return self.__str__()
