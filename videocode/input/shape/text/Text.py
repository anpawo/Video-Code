#!/usr/bin/env python3

from __future__ import annotations

import math
from copy import copy as _shallow_copy
import videocode.input.shape.text._TextHelper as _helper

from videocode.context import Context
from videocode.input.shape.Polygon import Polygon
from videocode.input.shape.Rectangle import Rectangle
from videocode.input.shape.Polygon import paint
from videocode.input.interface.Group import Group
from videocode.shader.ishader import FragmentShader, PaintShader
from videocode.input.shape.text.Letter import Letter
from videocode.shader.vertexShader.align import align
from videocode.shader.vertexShader.hide import hide
from videocode.shader.vertexShader.position import position
from videocode.shader.vertexShader.show import show
from videocode.shader.vertexShader.scale import scale
from videocode.utils.classutils import At
from videocode.utils.decorators import prop, propagate
from videocode.utils.bezier import Easing, easing as _easing
from videocode.ty import *
from videocode.constants import *
from videocode.utils.mixins import _hasFillStroke

__all__ = [
    "Letter",
    "Text",
]


# Padding (world units) added around the glyph bbox when auto-sizing a shader
# fill's canvas — purely internal: just enough that antialiased glyph edges
# don't get clipped at the canvas border.
_SHADER_CANVAS_MARGIN = 0.3


class Text(Group[Letter], _hasFillStroke):
    def __init__(
        self,
        text: str,
        fontSize: wnumber = 0.5,
        fontFamily: str = "Inter",
        fillColor: paint = WHITE,
        strokeColor: rgba = TRANSPARENT,
        strokeWidth: wufloat = 0,
        bold: bool = False,
        italic: bool = False,
    ):
        """
        `fillColor` may be a fragment shader instead of a color — the glyphs
        are then FILLED BY THE SHADER, one continuous pattern spread across
        the whole word:

            Text("STAR NEST", fontSize=1.7, fillColor=starNest())

        The shader is persistent fill state: it paints every frame from
        creation until `text.fillColor` is reassigned (to a color or another
        shader) or the video ends. Hiding/fading the text does NOT end it —
        the fill is simply not rendered while invisible and is still there
        when the text comes back. (Mechanics live in `Polygon`'s shader-fill
        segments; the timeline span resolves after the script ends.)

        Shader mode changes the structure: instead of per-letter inputs the
        Text holds ONE merged glyph silhouette (matte source, never drawn) +
        ONE canvas auto-sized to the word bbox — it positions/animates/hides
        as a single unit, but per-letter APIs (`typewriter`, letter access)
        don't apply. The shader only marches the canvas' coverage, so this is also
        the cheap way to run heavy math shaders. A letters-mode Text cannot
        switch to a shader fill after creation (recreate it instead).
        """
        self._shaderMode = isinstance(fillColor, PaintShader)
        self.text = text
        self.fontSize = fontSize
        self.fontFamily = fontFamily
        self.fillColor = fillColor
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth
        self.bold = bold
        self.italic = italic

        if isinstance(fillColor, PaintShader):
            # Lazy import: CompoundPolygon star-imports videocode, so a
            # module-level import here would be circular.
            from videocode.template.input.CompoundPolygon import CompoundPolygon

            # The glyphs are never drawn themselves — they only exist merged
            # into the matte source — so they must not register as inputs.
            with Context.noRegister():
                letters = Text(text, fontSize, fontFamily, WHITE, strokeColor, strokeWidth, bold, italic).inputs
            word = CompoundPolygon(*letters)

            # The canvas' fillColor IS the shader — Polygon's shader-fill
            # segments handle persistence and later reassignments.
            # Slightly larger than the glyph bbox so antialiased glyph edges
            # never get clipped at the canvas border.
            margin = _SHADER_CANVAS_MARGIN
            canvas = Rectangle(
                width=word.width + margin,
                height=word.height + margin,
                fillColor=fillColor,
                strokeColor=TRANSPARENT,
            )
            canvas.matte(word)

            # canvas + word grouped: the mask must travel with the pattern
            # (matte is screen-space) when the Text is moved/animated.
            super().__init__(canvas, word)
            return

        super().__init__(
            *(
                _helper.buildLetters(
                    text=text,
                    fontSize=fontSize,
                    fontFamily=fontFamily,
                    bold=bold,
                    italic=italic,
                    fillColor=fillColor,
                    strokeColor=strokeColor,
                    strokeWidth=strokeWidth,
                )
                if len(text) != 0
                else []
            )
        )
        self.alignLetters()

    def _distributeGradientColor(self, attr: str) -> None:
        value = getattr(self, attr)
        # Shader mode holds [canvas, word], not letters: forward the fill to
        # the CANVAS only (colors, gradients or another shader — Polygon's
        # shader-fill segments take over from this frame). The word is a pure
        # mask, and applying a shader to it would waste a fullscreen pass.
        if getattr(self, "_shaderMode", False):
            setattr(self.inputs[0], attr, value)
            return
        if isinstance(value, PaintShader):
            raise TypeError(
                "a letters-mode Text can't switch to a shader fill — create it "
                "with Text(..., fillColor=<shader>) instead (shader fills need "
                "the merged-silhouette structure)"
            )

        letters = self.inputs[: len(self.text)]
        if not letters:
            return

        color = getattr(self, attr)
        if not isinstance(color, LinearGradient):
            for l in letters:
                setattr(l, attr, color)
            return

        data = _helper.buildLetterData(self.text, self.fontSize, self.fontFamily, self.bold, self.italic)

        angleRad = math.radians(color.angle)
        dx, dy = math.cos(angleRad), math.sin(angleRad)

        def projRange(x: float, y: float, w: float, h: float) -> tuple[float, float]:
            projs = (x * dx + y * dy, (x + w) * dx + y * dy, x * dx + (y + h) * dy, (x + w) * dx + (y + h) * dy)
            return min(projs), max(projs)

        ranges = [projRange(x, y, l.width, l.height) for l, (_, x, y) in zip(letters, data)]
        globalMin = min(r[0] for r in ranges)
        globalMax = max(r[1] for r in ranges)
        globalRange = globalMax - globalMin

        for l, (letterMin, letterMax) in zip(letters, ranges):
            if globalRange < 1e-9:
                setattr(l, attr, color.colorAt(0))
            else:
                t0 = (letterMin - globalMin) / globalRange * 100
                t1 = (letterMax - globalMin) / globalRange * 100
                setattr(l, attr, color.slice(t0, t1))

    def _distributeFillColor(self) -> None:
        self._distributeGradientColor("fillColor")

    def _distributeStrokeColor(self) -> None:
        self._distributeGradientColor("strokeColor")

    @prop(onSet=_distributeFillColor)
    def fillColor() -> paint: ...

    @prop(onSet=_distributeStrokeColor)
    def strokeColor() -> rgba: ...

    @prop()
    def text() -> str: ...

    @text.setter
    def textSetter(self, value: str) -> None:
        l = len(self.inputs)
        r = len(value)
        if l > r:
            for i in range(l - r):
                self.inputs[-i - 1].hide()
        elif l < r:
            target = self.inputs[0].meta.transformationOffset if self.inputs else 0
            for i in range(r - l):
                newLetter = Letter(value[l + i], *self.config())
                if target > newLetter.meta.transformationOffset:
                    newLetter.hide()
                    newLetter.waitTo(target)
                    newLetter.show()
                self.inputs.append(newLetter)

        for i in range(min(l, r)):
            self.inputs[i].show()
            self.inputs[i].char = value[i]

        self.alignLetters()

    def config(self) -> tuple[wnumber, str, rgba, rgba, wnumber, bool, bool]:
        # Letters take a real color: in shader mode (fillColor is a shader,
        # painted on the canvas) hand them the opaque placeholder instead.
        fill = self.fillColor if isinstance(self.fillColor, rgba) else WHITE
        return (self.fontSize, self.fontFamily, fill, self.strokeColor, self.strokeWidth, self.bold, self.italic)

    def apply(self, *shaders, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self:
        for s in shaders:
            if isinstance(s, align):
                _s, _d, _o = s.resolve(start, duration, offset)
                _shallow_copy(s).modify(self)
                self.alignLetters(start=_s, duration=_d, offset=_o)
            elif getattr(self, "_shaderMode", False) and isinstance(s, FragmentShader):
                # Shader mode: a fragment shader POST-PROCESSES the filled
                # result — canvas only (touching the word would distort the
                # mask). Chain order is guaranteed: the fill is per-frame
                # state injected FIRST by the C++, timeline effects follow.
                self.inputs[0].apply(s, start=start, duration=duration, offset=offset)
            else:
                super().apply(s, start=start, duration=duration, offset=offset)
        return self

    def alignLetters(self, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> None:
        n = len(self.text)
        letters = self.inputs[:n]
        if not letters:
            return

        data = _helper.buildLetterData(
            text=self.text,
            fontSize=self.fontSize,
            fontFamily=self.fontFamily,
            bold=self.bold,
            italic=self.italic,
        )

        xMin = min(0.0, min(x for _, x, _ in data))
        xMax = max(x + l.width for (_, x, _), l in zip(data, letters))
        ax = xMin + self.meta.align.x * (xMax - xMin)

        ay = _helper.lineAnchor(self.fontFamily, self.bold, self.italic, self.fontSize, self.meta.align.y)

        for letter, (_, x, y) in zip(letters, data):
            letter.apply(align(0, 0))
            # Set text-local position directly on meta (no C++ push) so _regroup()
            # captures group-relative coords; _emitRigid below emits world positions.
            letter.meta.position = v2(x - ax, y - ay)

        # Re-snapshot member bases with the new text-local layout positions.
        self._regroup()
        # Emit world positions (group transform applied on top of text-local bases).
        self._emitRigid(start, duration, offset, pos=True)

        if isinstance(self.fillColor, LinearGradient):
            self._distributeFillColor()
        if isinstance(self.strokeColor, LinearGradient):
            self._distributeStrokeColor()

    @propagate(after=alignLetters)
    def fontSize() -> wnumber: ...
    @propagate(after=alignLetters)
    def fontFamily() -> str: ...
    @propagate(after=alignLetters)
    def bold() -> bool: ...
    @propagate(after=alignLetters)
    def italic() -> bool: ...

    @property
    def width(self) -> wunumber:
        if getattr(self, "_shaderMode", False):
            return self.inputs[0].width or 0  # the shader canvas
        return sum(l.width for l in self.inputs) if self.inputs else 0

    @property
    def height(self) -> wunumber:
        if getattr(self, "_shaderMode", False):
            return self.inputs[0].height or 0  # the shader canvas
        return max(l.height for l in self.inputs) if self.inputs else 0

    @classmethod
    def _fromLetters(cls, letters: list[Letter], src: Text) -> Text:
        """Wrap existing Letter objects in a Text — no letter rebuild, no alignLetters."""
        inst = object.__new__(cls)
        # Copy parent meta so zIndex/opacity/scale/rotation etc. are inherited;
        # clear index (virtual group, no C++ slot) and callbacks (not inherited).
        meta = _shallow_copy(src.meta)
        meta.index = cast(int, None)
        meta.preCallbacks = {}
        meta.postCallbacks = {}
        inst.meta = meta
        # prop init guard skips onSet on first assignment, so no side effects here
        inst.text = "".join(l.char for l in letters)
        inst.fontSize = src.fontSize
        inst.fontFamily = src.fontFamily
        inst.fillColor = src.fillColor
        inst.strokeColor = src.strokeColor
        inst.strokeWidth = src.strokeWidth
        inst.bold = src.bold
        inst.italic = src.italic
        inst.inputs = letters
        inst._snapshot()
        # Anchor group position at the leftmost letter; adjust member bases to stay relative.
        origin = v2(*letters[0].meta.position)
        meta.position = origin
        for _, base in inst._memberBases:
            base.position = base.position - origin
        return inst

    def findFirst(self, pattern: str) -> Text:
        results = self.find(pattern)
        return results.inputs[0]

    def find(self, pattern: str) -> Group[Text]:
        import re

        charToLetter: dict[int, int] = {}
        letterIdx = 0
        for charIdx, char in enumerate(self.text):
            if not char.isspace():
                charToLetter[charIdx] = letterIdx
                letterIdx += 1
        result: Group[Text] = Group()
        for match in re.finditer(pattern, self.text):
            letters = [self.inputs[charToLetter[i]] for i in range(match.start(), match.end()) if i in charToLetter]
            if letters:
                result.inputs.append(Text._fromLetters(letters, self))
        return result

    def typeInsert(self, pattern: str, *, start: sec = 0, delay: sec = SINGLE_FRAME) -> Self:
        """
        Reveals characters matching `pattern` one by one, shifting everything to
        their right to make room — as if typed inside existing text.
        """
        import re

        charToLetter: dict[int, int] = {}
        letterIdx = 0
        for charIdx, char in enumerate(self.text):
            if not char.isspace():
                charToLetter[charIdx] = letterIdx
                letterIdx += 1

        match = re.search(pattern, self.text)
        if not match:
            return self

        insertIdxs = [charToLetter[i] for i in range(match.start(), match.end()) if i in charToLetter]
        pushIdxs = [charToLetter[i] for i in range(match.end(), len(self.text)) if i in charToLetter]

        if not insertIdxs:
            return self

        data = _helper.buildLetterData(self.text, self.fontSize, self.fontFamily, self.bold, self.italic)
        xMin = min(x for _, x, _ in data)
        xMax = max(data[i][1] + self.inputs[i].width for i in range(len(data)))
        ax = xMin + self.meta.align.x * (xMax - xMin)
        ay = _helper.lineAnchor(self.fontFamily, self.bold, self.italic, self.fontSize, self.meta.align.y)

        insertXs = [data[li][1] for li in insertIdxs]
        pushStartX = data[pushIdxs[0]][1] if pushIdxs else (insertXs[-1] + self.inputs[insertIdxs[-1]].width)
        totalShift = pushStartX - insertXs[0]

        for li in insertIdxs:
            self.inputs[li].hide()
        for pli in pushIdxs:
            px = data[pli][1]
            py = data[pli][2]
            self.inputs[pli].apply(position(px - ax - totalShift, py - ay), start=0, duration=SINGLE_FRAME)

        for j, li in enumerate(insertIdxs):
            t = start + j * delay
            self.inputs[li].apply(show().at(start=t))
            nextX = insertXs[j + 1] if j + 1 < len(insertIdxs) else pushStartX
            partialShift = nextX - insertXs[0]
            for pli in pushIdxs:
                px = data[pli][1]
                py = data[pli][2]
                self.inputs[pli].apply(position(px - ax - totalShift + partialShift, py - ay), start=t, duration=SINGLE_FRAME)

        return self

    def typeIn(
        self,
        *,
        start: sec = 0,
        delay: sec = SINGLE_FRAME / 1.3,
        overshoot: float = 1.4,
        settle: sec = 3 * SINGLE_FRAME,
        easing: _easing = Easing.Out,
    ) -> Self:
        for i, letter in enumerate(self.inputs):
            tI = start + i * delay
            letter.apply(hide(), offset=0)
            letter.apply(show(), start=tI)
            if overshoot != 1.0:
                letter.apply(scale(overshoot, overshoot).at(start=tI))
                if settle < SINGLE_FRAME:
                    letter.apply(scale(1.0, 1.0).at(start=tI + SINGLE_FRAME))
                else:
                    letter.scaleTo(1.0, start=tI, duration=settle, easing=easing)
        return self

    def __str__(self) -> str:
        return f"Text({self.text})"
