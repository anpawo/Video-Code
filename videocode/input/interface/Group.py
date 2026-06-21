#!/usr/bin/env python3

from __future__ import annotations

import math
from copy import copy as _shallow_copy
from typing import Any
from typing_extensions import TypeVar
from videocode.input.input import *
from videocode.input.interface.Interface import Interface

_GROUP_T = TypeVar("_GROUP_T", bound=Input, default=Input)


class _MemberBase:
    def __init__(self, meta: Metadata) -> None:
        self.position = v2(*meta.position)
        self.rotation = meta.rotation
        self.scale = v2(*meta.scale)


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
        self._memberBases: list[tuple[Input, _MemberBase]] = [(m, _MemberBase(m.meta)) for m in self.inputs]

    def _regroup(self) -> None:
        """Re-snapshot member bases from their current meta (call after layout changes)."""
        self._snapshot()

    def _pivot(self) -> v2:
        """
        Pivot point in member-base space, determined by `meta.align`.

        Default align (0.5, 0.5) = center of the group's bounding box.
        This is the point that stays fixed when the group is rotated or scaled.
        """
        if not self._memberBases:
            return v2(0.0, 0.0)
        ax, ay = self.meta.align
        lefts = [base.position.x - m.width / 2 for m, base in self._memberBases]
        rights = [base.position.x + m.width / 2 for m, base in self._memberBases]
        bots = [base.position.y - m.height / 2 for m, base in self._memberBases]
        tops = [base.position.y + m.height / 2 for m, base in self._memberBases]
        return v2(
            min(lefts) + ax * (max(rights) - min(lefts)),
            min(bots) + ay * (max(tops) - min(bots)),
        )

    # ------------------------------------------------------------------
    # Rigid-body emission

    def _emitRigid(
        self,
        start: sec,
        duration: sec,
        offset: maybe[frame],
        *,
        pos: bool = False,
        rot: bool = False,
        scl: bool = False,
    ) -> None:
        """
        Emit concrete position/rotation/scale shaders to each member, applying the
        group's current accumulated transform on top of each member's frozen base.
        """
        if not self._memberBases:
            return

        gx, gy = self.meta.position
        grot_deg = self.meta.rotation
        gscale = self.meta.scale

        C = self._pivot()
        rad = math.radians(grot_deg)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)

        for m, base in self._memberBases:
            shaders: list[IShader] = []

            if pos:
                rx = base.position.x - C.x
                ry = base.position.y - C.y
                wx = rx * cos_r - ry * sin_r + C.x + gx
                wy = rx * sin_r + ry * cos_r + C.y + gy
                shaders.append(position(wx, wy))

            if rot:
                shaders.append(rotation(base.rotation + grot_deg))

            if scl:
                shaders.append(scale(*(base.scale + gscale - v2(1.0, 1.0))))

            if shaders:
                m.apply(*shaders, start=start, duration=duration, offset=offset)

    # ------------------------------------------------------------------
    # Interface

    def __iter__(self):
        for i in self.inputs:
            yield i

    def broadcast(self, func: Callable[[Input], Any]):
        for child in self.inputs:
            child.broadcast(func)

    def apply(self, *shaders: IShader, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self:
        for s in shaders:
            # Keep group.meta current even though groups never push to C++.
            # Subclasses and external code read group.meta.* directly —
            # e.g. Text.alignLetters reads self.meta.align.x, or user code
            # inspects text.meta.position to query the group's current logical state.
            # Groups are otherwise stateless — children own the rendering state.
            if isinstance(s, VertexShader):
                _shallow_copy(s).modify(self)

            if isinstance(s, (position, rotation, scale)):
                # Resolve the shader's own timing (.at(start=t) per animation frame)
                # before forwarding — each frame in a moveTo animation carries its own t.
                ts, td, to = s.resolve(start, duration, offset)
                if isinstance(s, position):
                    self._emitRigid(ts, td, to, pos=True)
                elif isinstance(s, rotation):
                    self._emitRigid(ts, td, to, pos=True, rot=True)
                else:
                    self._emitRigid(ts, td, to, scl=True)
            else:
                # All other shaders (color, opacity, args, translate, hide, …) broadcast
                # as-is to every member. i.apply() makes its own shallow copy for
                # VertexShaders before calling modify(), so passing s directly is safe.
                for i in self.inputs:
                    i.apply(s, start=start, duration=duration, offset=offset)

        return self

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

    @property
    def width(self) -> wnumber:
        if not self.inputs:
            return 0
        rights = [(inp.meta.position.x or 0) + inp.width / 2 for inp in self.inputs]
        lefts = [(inp.meta.position.x or 0) - inp.width / 2 for inp in self.inputs]
        return max(rights) - min(lefts)

    @property
    def height(self) -> wnumber:
        if not self.inputs:
            return 0
        tops = [(inp.meta.position.y or 0) + inp.height / 2 for inp in self.inputs]
        bots = [(inp.meta.position.y or 0) - inp.height / 2 for inp in self.inputs]
        return max(tops) - min(bots)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}"

    def __repr__(self) -> str:
        return self.__str__()
