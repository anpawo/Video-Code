#!/usr/bin/env python3

from __future__ import annotations

from videocode import *
from videocode.input.interface.Group import Group
from videocode.shader.vertexShader.position import position as _position
from videocode.shader.vertexShader.rotate import rotation as _rotation
from videocode.shader.vertexShader.scale import scale as _scale
from videocode.shader.vertexShader.zIndex import zIndex as _zIndex
from videocode.shader.vertexShader.opacity import opacity as _opacity

__all__ = ["Card", "CardStack"]

_POOL_Z = 200  # high enough to sit above ordinary scene elements
_CARD_W: float = 3.0
_CARD_H: float = 5.0  # 3:5 ratio (portrait / phone-like)

_Z_BG = 10  # card background
_Z_CONTENT = 11  # element, title, description


class Card(Group):
    """
    A structured card for use with :class:`CardStack`.

    A single background rectangle (black by default) with:
    - Top 3/5: ``element`` (any Input), auto-scaled to fit.
    - Bottom 2/5: ``title`` (required) + optional ``description``.

    Usage::

        card = Card(
            Image("photo.png"),
            title="My Title",
            description="A short subtitle",
        )
        stack = CardStack(card1, card2, card3)
    """

    def __init__(
        self,
        element: Input,
        title: str | Text,
        description: str | Text | None = None,
        *,
        cardWidth: wnumber = _CARD_W,
        cardHeight: wnumber = _CARD_H,
        bgColor: rgba = BLACK,
        borderColor: rgba = WHITE,
        borderWidth: wnumber = 0.035,
        titleFontSize: wnumber = 0.22,
        descFontSize: wnumber = 0.16,
        padding: wnumber = 0.5,
        cornerRadius: percent = 12,
    ):
        cw = float(cardWidth)
        ch = float(cardHeight)
        pad = float(padding)

        # — Background (full card) ———————————————————————————————————————
        bg = Rectangle(
            width=cw,
            height=ch,
            fillColor=bgColor,
            strokeColor=borderColor,
            strokeWidth=float(borderWidth),
            cornerRadius=cornerRadius,
        )
        bg.apply(_position(0.0, 0.0))
        bg.apply(_zIndex(_Z_BG))

        # — Element: top 3/5 of the card, auto-fit ———————————————————————
        elem_region_h = ch * 3.0 / 5.0
        elem_y = ch / 2.0 - elem_region_h / 2.0  # center of the top 3/5
        if isinstance(element, Group):
            # Layout bbox from member positions — Text overrides .width with
            # the glyph ink-width sum, which underestimates the laid-out span
            # (no inter-letter spacing) and would over-scale the element.
            elem_w = Group.width.fget(element)  # type: ignore[union-attr]
            elem_h = Group.height.fget(element)  # type: ignore[union-attr]
        else:
            elem_w = getattr(element, "width", None)
            elem_h = getattr(element, "height", None)
        if elem_w is not None and elem_h is not None:
            inner_w = cw - 2.0 * pad
            inner_h = elem_region_h - 2.0 * pad
            fit = min(inner_w / float(elem_w), inner_h / float(elem_h))
            element.apply(_scale(fit, fit))
        element.apply(_position(0.0, elem_y))
        element.apply(_zIndex(_Z_CONTENT))

        # — Title: bottom 2/5 of the card ————————————————————————————————
        if isinstance(title, str):
            title = Text(title, fontSize=float(titleFontSize), fillColor=WHITE)
        text_region_center = -(ch / 2.0 - ch / 5.0)  # center of the bottom 2/5
        if description is None:
            title_y = text_region_center
        else:
            title_y = text_region_center + float(titleFontSize)
        title.apply(_position(0.0, title_y))
        title.apply(_zIndex(_Z_CONTENT))

        members: list[Input] = [bg, element, title]

        # — Optional description —————————————————————————————————————————
        if description is not None:
            if isinstance(description, str):
                description = Text(description, fontSize=float(descFontSize), fillColor=WHITE | 0.6)
            desc_y = title_y - float(titleFontSize) * 1.5
            description.apply(_position(0.0, desc_y))
            description.apply(_zIndex(_Z_CONTENT))
            members.append(description)

        super().__init__(*members)


class CardStack(Group):
    """
    Tinder-style card deck.

    Cards are stacked with a slight downward + rightward offset and scale-down
    per rank behind. `.next()` fades the top card out (slight left shift + tilt)
    while the rest step forward; exited cards stay hidden — the deck depletes.

    Usage::

        c1 = Rectangle(width=3, height=5, fillColor=BLUE_C, cornerRadius=20)
        c2 = Rectangle(width=3, height=5, fillColor=RED_B,  cornerRadius=20)
        c3 = Rectangle(width=3, height=5, fillColor=GREEN_A, cornerRadius=20)
        stack = CardStack(c1, c2, c3).position(cx, cy)
        stack.next(start=1.0)
        stack.next(start=2.5)
    """

    def __init__(
        self,
        *cards: Input,
        offsetX: wnumber = 0.08,
        offsetY: wnumber = -0.15,
        stackScale: float = 0.95,
        visibleCount: int = 2,
    ):
        n = len(cards)
        self._cards: list[Input] = list(cards)
        self._offsetX = float(offsetX)
        self._offsetY = float(offsetY)
        self._stackScale = stackScale
        self._cx: float = 0.0
        self._cy: float = 0.0
        self._visibleCount = visibleCount

        for i, card in enumerate(self._cards):
            x, y, s = self._slot(i)
            card.apply(_position(x, y))
            card.apply(_scale(s, s))
            card.apply(_zIndex(_POOL_Z + (n - 1 - i)))
            if i > visibleCount:
                card.apply(_opacity(0))

        super().__init__(*cards)

    # -------------------------------------------------------------------------

    def _slot(self, rank: int) -> tuple[float, float, float]:
        """(x, y, scale) for a card at the given stack rank (0 = front)."""
        x = self._cx + rank * self._offsetX
        y = self._cy + rank * self._offsetY
        s = self._stackScale**rank
        return x, y, s

    # -------------------------------------------------------------------------

    def position(self, x: maybe[wnumber] = None, y: maybe[wnumber] = None, *, offset: maybe[frame] = None) -> Self:
        if x is not None:
            self._cx = float(x)
        if y is not None:
            self._cy = float(y)
        for i, card in enumerate(self._cards):
            cx, cy, _ = self._slot(i)
            card.apply(_position(cx, cy), offset=offset)
        return self

    # -------------------------------------------------------------------------

    def next(
        self,
        *,
        start: sec = 0,
        duration: sec = 0.5,
        easing: easing = Easing.Out,
    ) -> Self:
        n = len(self._cards)
        if n <= 1:
            return self

        top = self._cards[0]

        # — Exit: slight left shift + tilt + opacity decay ————————————————————
        # Position, rotation and opacity are applied together in a single
        # apply() per frame: the rigid-body emission reads the group's meta,
        # so splitting them into separate loops desyncs members (each loop
        # re-emits member positions from a meta already advanced to the
        # final value by the previous loop).
        src_pos = v2(*top.meta.position)
        src_rot = top.meta.rotation
        exit_pos = v2(src_pos.x - 1.5, src_pos.y - 0.3)

        posSeq = Easing.In.rangeIdx(src_pos, exit_pos, duration)
        rotSeq = Easing.In.rangeIdx(src_rot, src_rot - 12, duration)
        fadeSeq = Easing.In.rangeIdx(255.0, 0.0, duration)
        for (p, i), (r, _), (o, _) in zip(posSeq, rotSeq, fadeSeq):
            top.apply(_position(*p), _rotation(r), _opacity(o), start=start + i * SINGLE_FRAME)

        # — Advance: remaining cards each step one rank forward ————————————————
        # Position + scale in a single apply per frame (same desync reason as
        # the exit above — scale emission repositions members too).
        for rank, card in enumerate(self._cards[1:]):
            tx, ty, ts = self._slot(rank)
            stepPosSeq = easing.rangeIdx(v2(*card.meta.position), v2(tx, ty), duration)
            stepSclSeq = easing.rangeIdx(card.meta.scale.x, ts, duration)
            for (p, i), (s, _) in zip(stepPosSeq, stepSclSeq):
                card.apply(_position(*p), _scale(s, s), start=start + i * SINGLE_FRAME)

        # Fade in the card stepping into the last visible rank
        newly_visible_idx = self._visibleCount + 1
        if newly_visible_idx < n:
            newly_visible = self._cards[newly_visible_idx]
            for o, i in easing.rangeIdx(0.0, 255.0, duration):
                newly_visible.apply(_opacity(o), start=start + i * SINGLE_FRAME)

        # — Deplete: the exited card stays hidden and leaves the deck —————————
        self._cards = self._cards[1:]

        return self
