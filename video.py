#!/usr/bin/env python3

import math

from videocode import *
from videocode.template.effect.other.fillIn import fillIn
from videocode.template.effect.other.highlight import highlight
from videocode.template.input.YStack import Paragraphe
from videocode.template.input._inputs import *
from videocode.utils.bezier import _exponential, _exponentialDecay, _rushFrom, _smooth

PAUSE_DELAY = 0.4


def clearPara(para: Paragraphe) -> None:
    # back to the top, two lines down: under the import, which is never faded out
    para.curY = 0
    para.newline().newline()


def sceneRectangle(sv: SplitView, para: Paragraphe) -> Group:
    timestamp("code: create rectangle")
    para.add(textRect := Code("r = Rectangle(width=1.5, height=1)"))

    timestamp("show: rectangle")
    rect = Rectangle(width=1.5, height=1, cornerRadius=15, fillColor=BLUE_C, strokeColor=WHITE)
    dims = RectangleDimensions(rect).opacity(0)
    rect.position(sv.b.cx, sv.b.cy).opacity(0).waitFor(para).wait(PAUSE_DELAY).fadeIn()

    timestamp("show: rectangle dimensions")
    dims.waitFor(rect).wait(PAUSE_DELAY).fadeIn().flush()
    rect.waitFor(dims).wait(PAUSE_DELAY)

    timestamp("code: scale up rectangle")
    para.waitFor(rect).add(textScale := Code("r.scaleTo(factor=2, duration=0.6)"))

    timestamp("show: scale up rectangle")
    rect.waitFor(para).wait(PAUSE_DELAY).easeTogether(
        (rect.ref.width, rect.width * 2),
        (rect.ref.height, rect.height * 2),
        duration=0.6,
    )

    timestamp("show: hide dimensions")
    dims.waitFor(rect).wait(PAUSE_DELAY).fadeOut()

    timestamp("code: change rect fillcolor to red")
    para.waitFor(dims).wait(PAUSE_DELAY).newline()
    para.add(textFill1 := Code("r.fill(LinearGradient(RED, BLUE))"))
    para.add(textFill2 := Code("r.fill(LinearGradient(RED, GREEN))"))

    timestamp("show: rect fillcolor to red")
    rect.waitFor(para).wait(PAUSE_DELAY)
    for p in Easing.ExponentialDecay.range(0, 100, duration=2.4):
        rect.fillColor = LinearGradient((RED_B, p), BLUE_C)
        rect.flush()
    for p in Easing.ExponentialDecay.range(0, 50, duration=1.2):
        rect.fillColor = LinearGradient((RED_B, 100 - p), GREEN_A)
        rect.flush()

    return Group(textRect, textScale, textFill1, textFill2, rect)


def sceneBalls(sv: SplitView, para: Paragraphe) -> Group:
    timestamp("text: balls")
    para.add(textp1 := Code("p1 = Circle(radius=0.25)"))
    para.add(textp2 := Code("p2 = Circle(radius=0.25)"))
    para.add(textp3 := Code("p3 = Circle(radius=0.25)"))
    para.add(textBalls := Code("balls = XAlign(1.75, p1, p2, p3)"))
    para.newline()

    timestamp("show: balls")
    rad = 0.25
    gap = 1.75
    w = rad + gap
    p1 = Circle(radius=rad, fillColor=BLUE_C, strokeWidth=0.03)
    p2 = Circle(radius=rad, fillColor=BLUE_C, strokeWidth=0.03)
    p3 = Circle(radius=rad, fillColor=BLUE_C, strokeWidth=0.03)
    ltop = DashedLine(x1=sv.b.cx - w, y1=sv.b.cy + 2.5 + rad, x2=sv.b.cx + w, y2=sv.b.cy + 2.5 + rad, strokeWidth=0.04, color=WHITE | 0.5)
    lbot = DashedLine(x1=sv.b.cx - w, y1=sv.b.cy + 1 - rad, x2=sv.b.cx + w, y2=sv.b.cy + 1 - rad, strokeWidth=0.04, color=WHITE | 0.5)
    t1 = Text("InOut", fontSize=0.2)
    t2 = Text("ExpoDecay", fontSize=0.2)
    t3 = Text("Expo", fontSize=0.2)

    g1 = FunctionGraph(_smooth, (0, 1))
    g2 = FunctionGraph(_exponentialDecay, (0, 1))
    g3 = FunctionGraph(_exponential, (0, 1))

    pts = XAlign[Circle](gap, p1, p2, p3).position(sv.b.cx, sv.b.cy + 1)
    txt = XAlign(gap, t1, t2, t3).position(sv.b.cx, sv.b.cy)
    grs = XAlign(gap, g1, g2, g3).position(sv.b.cx - 0.5, sv.b.cy - 1.5)
    g = Group(ltop, lbot, pts, txt, grs).opacity(0).waitFor(para).wait(PAUSE_DELAY).fadeIn().wait(PAUSE_DELAY * 2)

    timestamp("text: move balls")
    para.waitFor(g).wait(PAUSE_DELAY)
    para.add(textb1 := Code("for i, input in enumerate(balls):"))
    para.add(textb2 := Code("    ease = [Smooth, ExpoDecay, Expo][i]"))
    para.add(textb3 := Code("    input.moveBy(y=+1.5, easing=ease).flush()"))
    para.add(textb4 := Code("    input.moveBy(y=-1.5, easing=ease).flush()"))

    timestamp("show: move balls")
    pts.waitFor(para).wait(PAUSE_DELAY * 2)
    for i, input in enumerate(pts):
        ease = [Easing.Smooth, Easing.ExponentialDecay, Easing.Exponential][i]
        input.moveBy(y=1.5, easing=ease, duration=2).wait(PAUSE_DELAY).moveBy(y=-1.5, easing=ease, duration=2).flush()

    return Group(textp1, textp2, textp3, textBalls, textb1, textb2, textb3, textb4, g)


def sceneText(sv: SplitView, para: Paragraphe) -> Group:
    timestamp("text")
    para.add(textnbr1 := Code('nbr = Text("125376890123")')).newline()
    nbr = Text("125376890123", fontSize=0.4).position(sv.b.x, sv.b.y).opacity(0).waitFor(para).fadeIn().flush()

    timestamp("text highlight")
    para.waitFor(nbr).add(textnbr2 := Code('twelve = nbr.find("12")'))
    para.add(textnbr3 := Code("twelve.apply(highlight())"))
    nbr.waitFor(para).wait(PAUSE_DELAY * 2).find("12").apply(highlight())
    nbr.waitForOthers().wait(PAUSE_DELAY)

    timestamp("text radiant")
    para.waitFor(nbr).newline().add(textnbr4 := Code("nbr.apply(fillIn(LinearGradient(BLUE, RED)))"))
    # Not `.fill()`: easing between two gradients interpolates their COLORS
    # stop by stop (and needs matching stop counts), so it can never slide a
    # boundary. fillIn sweeps one.
    nbr.waitFor(para).wait(PAUSE_DELAY).apply(fillIn(LinearGradient(BLUE_C, RED_B), duration=1.6))

    return Group(nbr, textnbr1, textnbr2, textnbr3, textnbr4)


def sceneRectShader(sv: SplitView, para: Paragraphe) -> Group:
    timestamp("rect fire")
    # a shader fill is fill state, set at creation: a letters-mode Text (nbr, via find) can't switch to one
    para.add(textfire1 := Code("s = Square(4, cornerRadius=15, fillColor=starNest())")).newline()
    # Sized to the panel, not to 16x9: stacking leaves `b` only ~2.6 units tall
    # in a landscape frame, so a hardcoded side=4 spills out of it. Capped at 4
    # so the wide layout is unchanged — this only ever shrinks.
    side = min(4, sv.b.innerWidth, sv.b.innerHeight)
    sqrBg = (
        Square(side=side, cornerRadius=15, fillColor=starNest(scale=0.75, origin=(150, 100), space=Space.ANCHOR))
        .position(sv.b.x, sv.b.y)
        .opacity(0)
        .scale(0.85)
        .waitFor(para)
        .wait(PAUSE_DELAY)
        .fadeIn(duration=PAUSE_DELAY * 1.5)
        .scaleTo(factor=1, duration=PAUSE_DELAY)
    )

    timestamp("text: morph square -> hexagon")
    para.waitFor(sqrBg).wait(PAUSE_DELAY)
    para.add(textfire2 := Code("s.morphTo(6, duration=2)")).newline()

    timestamp("show: morph square -> hexagon")
    sqrBg.waitFor(para).wait(PAUSE_DELAY)
    sqrBg.morphTo(6, duration=2).wait(PAUSE_DELAY)

    timestamp("text: morph hexagon -> square")
    para.waitFor(sqrBg).wait(PAUSE_DELAY)
    para.add(textfire3 := Code("s.morphTo(4, duration=2)"))

    timestamp("show: morph hexagon -> square")
    sqrBg.waitFor(para).wait(PAUSE_DELAY)
    sqrBg.morphTo(4, duration=2)

    wait(3)

    return Group(textfire1, textfire2, textfire3, sqrBg)


def sceneImage(sv: SplitView, para: Paragraphe) -> Group:
    timestamp("text: image")
    para.add(textImg1 := Code('img = Image("white_bishop.png")')).newline()
    para.add(textImg2 := Code("img.fadeIn().scaleTo(2)")).newline()

    timestamp("show: image")
    img = Image("wb.png").position(sv.b.x, sv.b.y).opacity(0).waitFor(para).wait(PAUSE_DELAY).fadeIn().scaleTo(2).flush()
    # problem to fix here, im forced to add opacity(0) because the image appears before the effects are sent. maybe its meant

    timestamp("text: image lightsweep")
    para.waitFor(img).wait(PAUSE_DELAY).add(textImg3 := Code("img.apply(lightSweep(width=10), duration=2)")).newline()

    timestamp("show: image lightsweep")
    img.waitFor(para).wait(PAUSE_DELAY).apply(lightSweep(width=10), duration=1.6).flush()

    # timestamp("text: image blur")
    # para.waitFor(img).wait(PAUSE_DELAY).add(textImg3 := Code("img.apply(blur(5), duration=2)"))

    # timestamp("show: image blur")
    # img.waitFor(para).wait(PAUSE_DELAY).apply(blur(5), duration=2)

    return Group(
        textImg1,
        textImg2,
        textImg3,
        img,
    )


def sceneGroup(sv: SplitView, para: Paragraphe) -> Group:
    timestamp("square")
    para.wait(PAUSE_DELAY).add(textG1 := Code("s = Square()"))
    s = Square(side=1, cornerRadius=15, fillColor=BLUE_C, strokeColor=WHITE).opacity(0).waitFor(para).position(sv.b.x, sv.b.y).fadeIn()
    timestamp("move square")
    para.waitFor(s).wait(PAUSE_DELAY).add(textG2 := Code("s.moveBy(x=-1)"))
    s.waitFor(para).moveBy(x=-1.25)

    timestamp("circle")
    para.waitFor(s).wait(PAUSE_DELAY).newline().add(textG3 := Code("c = Circle()"))
    c = Circle(radius=0.5, fillColor=RED_B, strokeColor=WHITE).opacity(0).waitFor(para).position(sv.b.x, sv.b.y).fadeIn()
    timestamp("move circle")
    para.waitFor(c).wait(PAUSE_DELAY).add(textG4 := Code("c.moveBy(x=1)"))
    c.waitFor(para).moveBy(x=1.25)

    timestamp("group")
    para.newline().waitFor(c).wait(PAUSE_DELAY).add(textG5 := Code("g = Group(s, c)"))
    timestamp("group scale down + rotate")
    para.wait(PAUSE_DELAY).add(textG6 := Code("g.rotateBy(180).scaleTo(0.5)"))
    g = Group(s, c).waitFor(para).wait(PAUSE_DELAY).scaleTo(0.5, duration=1.2).rotateBy(180, duration=1.2)

    return Group(textG1, textG2, textG3, textG4, textG5, textG6, s, c)


def main() -> None:
    sv = SplitView(ratio=5 / 9, split=Split.COLUMNS)
    # sv = SplitView(ratio=3.5 / 3, split=Split.ROWS)
    para = Paragraphe(gap=0.18).position(x=sv.a.left, y=sv.a.top)

    # shown for the whole video, kept by every clearPara
    para.add(Code("from videocode import *")).newline()

    scenes = [
        # sceneRectangle,
        # sceneBalls,
        # ----
        sceneGroup,
        sceneText,
        sceneImage,
        sceneRectShader,
    ]

    prev = None
    for scene in scenes:
        if prev is not None:
            para.waitFor(prev)
        prev = scene(sv, para)
        if scene is not scenes[-1]:
            timestamp(f"show: cleanup {scene.__name__}")
            prev.waitForOthers().wait(PAUSE_DELAY * 2).fadeOut()
            clearPara(para)

    # bg — created last so drift() starts at the end of existing content
    Plane().drift()


main()
