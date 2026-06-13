#!/usr/bin/env python3


from copy import copy as _shallow_copy
from typing import Callable, TypeVar
from videocode.input.input import *
from videocode.input.interface.Group import Group
from videocode.shader.vertexShader.translate import translate


_GROUP_T = TypeVar("_GROUP_T", bound=Input, default=Input)


class _Snapshot:
    """A member's `position`/`scale`/`rotation`/`opacity`/`align`, captured once."""

    __slots__ = ("position", "scale", "rotation", "opacity", "align")

    position: v2[wnumber, wnumber]
    scale: v2[wnumber, wnumber]
    rotation: number
    opacity: number
    align: v2[wnumber, wnumber]

    def __init__(self, meta: Metadata) -> None:
        self.position = v2(*meta.position)
        self.scale = v2(*meta.scale)
        self.rotation = meta.rotation
        self.opacity = meta.opacity
        self.align = v2(*meta.align)


def _withTiming(template: IShader, target: IShader) -> IShader:
    target.start, target.duration, target.offset = template.start, template.duration, template.offset
    return target


class StatefulGroup(Group[_GROUP_T]):
    """
    A `Group` that remembers each member's base metadata (position, scale,
    rotation, opacity, align) as of `StatefulGroup` creation.

    `Group.apply()` broadcasts each shader as-is, so members that already
    diverged from one another (e.g. different starting `scale`) get collapsed
    onto the same absolute value. `StatefulGroup` instead tracks how far the
    group's own logical value has moved since creation and re-applies that
    same delta on top of each member's own snapshot — members that diverged
    at creation stay diverged.
    """

    def __init__(self, *inputs: _GROUP_T):
        super().__init__(*inputs)
        self._snapshots: dict[Input, _Snapshot] = {}

        def snapshot(i: Input) -> None:
            self._snapshots[i] = _Snapshot(i.meta)

        self.broadcast(snapshot)
        self._groupSnapshot = _Snapshot(self.meta)

    def apply(self, *shaders: IShader, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self:
        for s in shaders:
            if isinstance(s, VertexShader):
                _shallow_copy(s).modify(self)

            target: Callable[[_Snapshot], VertexShader] | None = None

            if isinstance(s, (position, translate)):
                positionDelta = self.meta.position - self._groupSnapshot.position
                target = lambda snap: position(*(snap.position + positionDelta))
            elif isinstance(s, scale):
                scaleDelta = self.meta.scale - self._groupSnapshot.scale
                target = lambda snap: scale(*(snap.scale + scaleDelta))
            elif isinstance(s, rotation):
                rotationDelta = self.meta.rotation - self._groupSnapshot.rotation
                target = lambda snap: rotation(snap.rotation + rotationDelta)
            elif isinstance(s, opacity):
                opacityDelta = self.meta.opacity - self._groupSnapshot.opacity
                target = lambda snap: opacity(snap.opacity + opacityDelta)
            elif isinstance(s, align):
                alignDelta = self.meta.align - self._groupSnapshot.align
                target = lambda snap: align(*(snap.align + alignDelta))

            if target is None:
                for i in self.inputs:
                    i.apply(s, start=start, duration=duration, offset=offset)
                continue

            for child, snap in self._snapshots.items():
                child.apply(_withTiming(s, target(snap)), start=start, duration=duration, offset=offset)
        return self
