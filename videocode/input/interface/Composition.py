#!/usr/bin/env python3

from __future__ import annotations

from copy import copy as _shallow_copy
from typing import Self

from videocode.constants import SINGLE_FRAME, TRANSPARENT, WORLD_HEIGHT, WORLD_WIDTH
from videocode.context import Context
from videocode.input.input import Input
from videocode.input.interface.Group import Group
from videocode.input.shape.Rectangle import Rectangle
from videocode.shader.ishader import Effect, FragmentShader, GroupEffect, IShader, VertexShader
from videocode.shader.vertexShader.blendMode import blendMode
from videocode.shader.vertexShader.comp import comp as _compShader
from videocode.shader.vertexShader.compMember import compMember
from videocode.shader.vertexShader.hide import hide
from videocode.shader.vertexShader.matte import matte
from videocode.shader.vertexShader.opacity import opacity
from videocode.shader.vertexShader.show import show
from videocode.shader.vertexShader.zIndex import zIndex
from videocode.ty import frame, maybe, sec


class Composition(Group):
    """
    A `Group` that renders as ONE layer.

    The name is the industry's: a composition, in After Effects and everything
    that followed it, is exactly this — a container whose contents are rendered
    as a single image and which can be nested. `Comp` is the abbreviation
    everyone actually says, and it is an alias at the foot of this file.

    An ordinary group is a bookkeeping convenience: its members are still
    drawn one by one, so a `Group(a, b).fadeOut()` fades each of them
    separately and wherever they overlap you see through one into the other.
    A `Composition` draws its members into a layer of their own first, then puts that
    single layer on the frame — so the fade, the effects and the mask land on
    the picture the members make together::

        badge = Composition(Circle(radius=1), Square(side=1.4))
        badge.fadeOut(duration=1)          # ONE fade, no grey patch at the overlap
        badge.apply(blur(radius=6))        # blurs the pair, not each shape
        badge.moveBy(x=3)                  # members still move rigidly, as in any Group

    It is also the answer to "mask this text": a multi-letter `Text` is a group
    of letters with no single index, and a matte source has to be one input.
    Wrapped in a `Composition` it is one::

        Rectangle(width=12, height=3, fillColor=RAINBOW).matte(Composition(*Text("MATTE").inputs))

    Transforms (`moveTo`, `rotateBy`, `scaleTo`, `align`) stay `Group`'s rigid
    orbital ones on the members — the composite would only let you scale
    pixels. Everything that is about COMPOSITING — opacity, fragment effects,
    `matte`, `zIndex`, `blendMode`, `hide`/`show` — lands on the comp's own
    layer, which is where "as one layer" is decided.

    The comp composites at its own `zIndex`, which defaults to just above its
    last member, and its members no longer take part in the frame's z-order on
    their own: pulling things into a comp makes them one layer, at one depth.

    A member that is itself semi-transparent loses some colour to the flatten
    (a 50% white square reads 90 rather than 153), which is what every isolated
    layer in this engine does today — the same number comes out of any effect
    layer, comp or not. Comps stack all the same, and an opaque member is exact.
    """
    # ponytail: that colour loss is the transparent-clear composite; the fix is
    # premultiplied-alpha blending in every isolated layer, which moves goldens
    # across the whole suite. Do it deliberately, not as a comp side effect.

    #: Claims that belong to the LAYER rather than to the members. Everything
    #: else — colour, args, the rigid transforms — is still `Group`'s business.
    _LAYER_CLAIMS = (FragmentShader, opacity, matte, zIndex, blendMode, hide, show)

    def __init__(self, *inputs: Input):
        super().__init__(*inputs)
        # A full-frame invisible input, like AdjustmentLayer: never painted, but
        # its box is what bbox-driven effects (crop, vignette) resolve against.
        # Built AFTER the members, so its default zIndex — creation order — puts
        # the composite just above them, which is where they were.
        self.layer = Rectangle(
            width=WORLD_WIDTH,
            height=WORLD_HEIGHT,
            fillColor=TRANSPARENT,
            strokeColor=TRANSPARENT,
            strokeWidth=0,
        ).apply(_compShader())

        # A comp answers with its LAYER's slot when something asks which input
        # it is. `matte(comp)` is the case that needs it — a matte source must
        # be one index, and the layer is the one the members were flattened
        # into. Inert otherwise: a Group never writes to a slot of its own,
        # `Composition.apply` routes every claim to the layer or to the members.
        self.meta.index = self.layer.meta.index

        member = compMember(self.layer)
        for i in self.inputs:
            # A nested comp joins as its LAYER, not as its leaves: its members
            # are already spoken for, and re-marking them would move them into
            # the outer comp and lose the inner one's own fade.
            if isinstance(i, Composition):
                i.layer.apply(member)
            else:
                i.broadcast(lambda m: m.apply(member))

    def _cursor(self) -> frame:
        """Where the comp's own timeline stands: the latest of everything in it."""
        cursors = [self.layer.meta.transformationOffset, Context.waitOffset]
        self.broadcast(lambda i: cursors.append(i.meta.transformationOffset))
        return max(cursors)

    def apply(self, *shaders: IShader | Effect | GroupEffect, start: sec = 0, duration: sec = SINGLE_FRAME, offset: maybe[frame] = None) -> Self:
        """
        Split the claim: compositing lands on the layer, the rest on the members.

        A `Composition` is a `Group` for everything a group is good at — the rigid
        transforms, the member-aware effects — and its own input for the four
        things that only mean something once the members are one picture.
        """
        mine: list[IShader] = []
        theirs: list[IShader | Effect | GroupEffect] = []
        for s in shaders:
            # Split by identity, not by `in`: two equal-looking shaders in one
            # call are two claims, and `x in list` would move both or neither.
            (mine if isinstance(s, self._LAYER_CLAIMS) else theirs).append(s)  # type: ignore[arg-type]
        if theirs:
            super().apply(*theirs, start=start, duration=duration, offset=offset)
        if not mine:
            return self
        for s in mine:
            # The group's own meta stays truthful even though the claim goes
            # elsewhere: `fadeOut()` reads `self.meta.opacity` to know where the
            # fade starts, and `Group.apply` would have done this for us.
            if isinstance(s, VertexShader):
                _shallow_copy(s).modify(self)
        # The layer has no cursor of its own until it is written to, and a comp
        # animation has to open where its members already are — `a.fadeIn();
        # a.flush()` then `comp.fadeOut()` must not rewind to frame 0. Taking
        # the max INCLUDES Context.waitOffset, so pinning the offset here can
        # never override a pending global wait().
        self.layer.apply(*mine, start=start, duration=duration, offset=self._cursor() if offset is None else offset)
        return self


#: What everyone says out loud. The class carries the whole word so that a
#: scene reads as the trade does; the short form is here because nobody types
#: eleven letters in the middle of a line.
Comp = Composition
