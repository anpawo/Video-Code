#!/usr/bin/env python3

from __future__ import annotations

from videocode import *
from videocode.input.interface.Group import Group
from videocode.shader.vertexShader.args import args as _Args
from videocode.shader.vertexShader.hide import hide as _Hide
from videocode.shader.vertexShader.opacity import opacity as _Opacity
from videocode.shader.vertexShader.position import position as _Position
from videocode.shader.vertexShader.scale import scale as _Scale
from videocode.shader.vertexShader.show import show as _Show
from videocode.template.input.Arrow import DoubleArrow

__all__ = ["RectangleDimensions"]


def _fmt(v: float) -> str:
    return f"{v:.1f}"


class RectangleDimensions(Group):
    """
    Annotates a Rectangle with dimension arrows and labels.

    widthArrow:  horizontal DoubleArrow above the top border
    heightArrow: vertical DoubleArrow to the right of the right border
    widthLabel:  Text showing current width, above the width arrow
    heightLabel: Text showing current height, right of the height arrow

    Being a Group, you can broadcast shaders to all annotations at once:
    ``dim.hide()`` / ``dim.show()`` / ``dim.opacity(0.5)``.

    Callbacks are registered on `rect` so all annotations update automatically
    when rect.width, rect.height, or rect.position changes — including
    per-frame during ease() animations.  Concurrent ease("width") and
    ease("height") calls work correctly because each callback only touches
    its own dimension's dependent annotations.

    Usage::

        rect = Rectangle(width=3, height=2)
        dim  = RectangleDimensions(rect)
        # add to scene: rect, dim
        rect.ease("height", 4, duration=1.5, easing=Easing.ThereAndBack)\\
            .ease("width", 1.5, start=0.75, duration=1.5, easing=Easing.ThereAndBack)
    """

    def __init__(
        self,
        rect: Rectangle,
        gap: wufloat = 0.2,
        color: rgba = WHITE,
        fontSize: wnumber = 0.2,
    ):
        self.rect = rect
        self._gap = gap
        self._fontSize = fontSize

        rx: wnumber = rect.meta.position.x
        ry: wnumber = rect.meta.position.y
        rw: wnumber = rect.width * (rect.meta.scale.x or 1)
        rh: wnumber = rect.height * (rect.meta.scale.y or 1)

        # Cached visual state — each callback updates only its own field,
        # so sibling callbacks never read a stale cross-dimension value.
        self._rx: wnumber = rx
        self._ry: wnumber = ry
        self._rw: wnumber = rw
        self._rh: wnumber = rh
        # Maps abs_frame → rh at that frame so _syncWidthChanged can restore the
        # correct widthLabel Y when it overlaps with a concurrent height animation.
        self._rh_at_frame: dict[int, float] = {}

        self.widthArrow = DoubleArrow(length=rw, fillColor=color).position(rx, ry + rh / 2 + gap)
        self.widthLabel = Text(_fmt(rw), fontSize=fontSize, fillColor=color).align(y=0).position(rx, ry + rh / 2 + gap)

        self.heightArrow = DoubleArrow(length=rh, fillColor=color).rotation(90).position(rx + rw / 2 + gap, ry)
        self.heightLabel = Text(_fmt(rh), fontSize=fontSize, fillColor=color).align(x=0).position(rx + rw / 2 + gap, ry)

        def _on_args(s: _Args, start: sec, duration: sec, offset: frame) -> None:
            if s.name != "points":
                return
            new_rw = self.rect.width * (self.rect.meta.scale.x or 1)
            new_rh = self.rect.height * (self.rect.meta.scale.y or 1)
            resolved = s.resolve(start, duration, offset)
            if new_rw != self._rw:
                self._rw = new_rw
                self._syncWidthChanged(*resolved)
            if new_rh != self._rh:
                self._rh = new_rh
                self._syncHeightChanged(*resolved)

        def _on_position(s: _Position, start: sec, duration: sec, offset: frame) -> None:
            self._rx = self.rect.meta.position.x
            self._ry = self.rect.meta.position.y
            self._syncPositions(*s.resolve(start, duration, offset))

        def _on_scale(s: _Scale, start: sec, duration: sec, offset: frame) -> None:
            new_rw = self.rect.width * (self.rect.meta.scale.x or 1)
            new_rh = self.rect.height * (self.rect.meta.scale.y or 1)
            resolved = s.resolve(start, duration, offset)
            if new_rw != self._rw:
                self._rw = new_rw
                self._syncWidthChanged(*resolved)
            if new_rh != self._rh:
                self._rh = new_rh
                self._syncHeightChanged(*resolved)

        def _on_opacity(s: _Opacity, start: sec, duration: sec, offset: frame) -> None:
            self._applyResolved(_Opacity(s.opacity), s.resolve(start, duration, offset))

        rect.addPostCallback(_Args, _on_args)
        rect.addPostCallback(_Position, _on_position)
        rect.addPostCallback(_Scale, _on_scale)
        # rect.addPostCallback(_Opacity, _on_opacity)

        super().__init__(self.widthArrow, self.widthLabel, self.heightArrow, self.heightLabel)

    # ------------------------------------------------------------------
    # Internals

    def _applyResolved(self, shader: IShader, timing: tuple[sec, sec, maybe[frame]]) -> None:
        start, duration, offset = timing
        self.apply(shader, start=start, duration=duration, offset=offset)

    def _rebuildPoints(self, arrow: DoubleArrow, new_length: float) -> list[point]:
        """Set arrow length and rebuild its control points without pushing to Context."""
        object.__setattr__(arrow, "_length", new_length)
        arrow.vertices = arrow.generateVertices()
        pts = arrow.buildPoints()
        object.__setattr__(arrow, "points", pts)
        return pts

    def _updateLabel(self, label: Text, text: str, abs_frame: frame) -> None:
        """Update label text and re-align letters at abs_frame."""
        saved: dict[int, int] = {}

        def _set(i: Input) -> None:
            saved[id(i.meta)] = i.meta.transformationOffset
            i.meta.transformationOffset = abs_frame
            i.meta.pendingOffset = abs_frame
            i.meta.pendingStart = 0

        def _clear(i: Input) -> None:
            i.meta.pendingOffset = None
            i.meta.pendingStart = 0
            i.meta.transformationOffset = saved[id(i.meta)]

        label.broadcast(_set)
        label.text = text
        label.broadcast(_clear)
        label.alignLetters(start=0, duration=SINGLE_FRAME, offset=abs_frame)

    def _syncWidthChanged(self, start: sec, duration: sec, offset: maybe[frame]) -> None:
        """Push only width-dependent annotations.

        - widthArrow geometry (length = rw)
        - widthLabel text
        - heightArrow X position  (rx + rw/2 + gap)
        - heightLabel X position

        Does NOT touch widthArrow/widthLabel Y — those depend only on height
        and are managed by _syncHeightChanged.
        """
        rw = self._rw
        rx = self._rx
        ry = self._ry
        gap = self._gap
        fs = self._fontSize
        abs_frame = round(start * FRAMERATE) + (offset if offset is not None else 0)

        wa_pts = self._rebuildPoints(self.widthArrow, rw)
        self.widthArrow.apply(_Args("points", wa_pts), start=start, duration=duration, offset=offset)

        # alignLetters inside _updateLabel reads widthLabel.meta.position.y.
        # During overlap with a height animation, that value is stale (height
        # ThereAndBack already returned, so meta.position.y is back to original).
        # Restore the correct Y for this abs_frame before alignLetters fires.
        rh_here = self._rh_at_frame.get(abs_frame, self._rh)
        self.widthLabel.meta.position = v2(rx, ry + rh_here / 2 + gap + fs * 0.6)
        self._updateLabel(self.widthLabel, _fmt(rw), abs_frame)

        self.heightArrow.apply(_Position(rx + rw / 2 + gap, ry), start=start, duration=duration, offset=offset)
        self.heightLabel.apply(_Position(rx + rw / 2 + gap + fs * 0.7, ry), start=start, duration=duration, offset=offset)

    def _syncHeightChanged(self, start: sec, duration: sec, offset: maybe[frame]) -> None:
        """Push only height-dependent annotations.

        - heightArrow geometry (length = rh)
        - heightLabel text
        - widthArrow Y position  (ry + rh/2 + gap)
        - widthLabel Y position

        Does NOT touch heightArrow/heightLabel X — those depend only on width
        and are managed by _syncWidthChanged.
        """
        rh = self._rh
        rx = self._rx
        ry = self._ry
        gap = self._gap
        fs = self._fontSize
        abs_frame = round(start * FRAMERATE) + (offset if offset is not None else 0)

        self._rh_at_frame[abs_frame] = rh

        ha_pts = self._rebuildPoints(self.heightArrow, rh)
        self.heightArrow.apply(_Args("points", ha_pts), start=start, duration=duration, offset=offset)

        self._updateLabel(self.heightLabel, _fmt(rh), abs_frame)

        self.widthArrow.apply(_Position(rx, ry + rh / 2 + gap), start=start, duration=duration, offset=offset)
        self.widthLabel.apply(_Position(rx, ry + rh / 2 + gap + fs * 0.6), start=start, duration=duration, offset=offset)

    def _syncPositions(self, start: sec, duration: sec, offset: maybe[frame]) -> None:
        """Reposition all annotations when the rect moves (no geometry change)."""
        rw = self._rw
        rh = self._rh
        rx = self._rx
        ry = self._ry
        gap = self._gap
        fs = self._fontSize

        self.widthArrow.apply(_Position(rx, ry + rh / 2 + gap), start=start, duration=duration, offset=offset)
        self.widthLabel.apply(_Position(rx, ry + rh / 2 + gap + fs * 0.6), start=start, duration=duration, offset=offset)
        self.heightArrow.apply(_Position(rx + rw / 2 + gap, ry), start=start, duration=duration, offset=offset)
        self.heightLabel.apply(_Position(rx + rw / 2 + gap + fs * 0.7, ry), start=start, duration=duration, offset=offset)
