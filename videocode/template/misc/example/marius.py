#!/usr/bin/env python3


import math


from videocode.template.input.Arrow import Arrow
from videocode.template.input.Graph import *
from videocode.template.input.Plane import Plane
from videocode.template.misc.chess.chessboard import ChessBoard
from videocode import *


def example0():
    example1().fadeOut()
    wait()
    example2()  # already fadedOut
    wait()
    example3().fadeOut()
    wait()
    example4()


def example1():
    """
    Basic Inputs
    """
    timestamp("Example #1: All Basic Inputs / Shapes")

    plane = Plane()

    rect = Rectangle(height=2, width=4).position(x=-7)
    circle = Circle(radius=1).position(x=-2)
    sqrRounded = Square(side=2, cornerRadius=30).position(x=1)
    triRandom = Triangle().position(x=4)

    img = Offset(0, 0.5, Image("wb.png").position(x=-6.5))
    text = Text("Hello World", fontSize=0.75).position(x=-5.075)
    triEqui = EquilateralTriangle(side=1, strokeColor=TRANSPARENT).position(x=0)
    triRight = RightTriangle(width=1, height=1).position(x=2)
    triEquiRounded = EquilateralTriangle(side=1, cornerRadius=30).position(x=4)
    arrow = Arrow().position(x=6.5, y=0.5)

    all = (
        Group(
            plane,
            Group(rect, sqrRounded, triRandom, circle).align(x=0, y=0).position(y=2),
            Group(text, triEqui, triRight, triEquiRounded).align(x=0, y=0).addInput(img).position(y=0).addInput(arrow),
        )
        .fadeIn()
        .waitForOthers(0.5, updateContext=True)
    )

    return all


def example2():
    """
    Carré qui apparait en grandissant puis qui bouge sur la droite et disparait en grandissant.

    Square that appears by growing, then moves to the right and disappears by growing.
    """
    timestamp("Example #2: Little Square Animation")

    return (
        Square(
            side=2,
            cornerRadius=30,
        )
        .position(x=-2)
        .scale(0.1)
        .scaleTo(1)
        .flush()
        .moveTo(x=2)
        .flush()
        .fadeOut(hide=True)
        .scaleTo(2)
        .flush()
    )


def example3():
    """
    Ligne qui s'étend sur la longueur puis sur la largeur puis qui devient plus foncé.
    Un peu comme une TV ou un paragraphe de texte dans Pokémon.

    Line that extends in length then in height then becomes darker.
    Similar to a TV turning on or a paragraph of text appearing in Pokémon.
    """
    timestamp("Example #3: Game Dialogue")

    s = HorizontalLine(length=0, strokeColor=WHITE, fillColor=DARK_BLUE | 0.5)
    s.ease(s.ref.width, 6).flush()
    s.easeTogether(
        (s.ref.height, 2.5),
        (s.ref.cornerRadius, 15, Easing.Out),
        (s.ref.strokeWidth, 0.05, Easing.Out),
    ).flush()
    s.ease(s.ref.fillColor, DARK_BLUE | 0.25, easing=Easing.Out).flush()

    wait()

    t = Text("Hello World!").fadeIn()

    return Group(s, t).waitForOthers(updateContext=True)


def example4():
    """
    First Quadrant of a Cartesian Graph.
    """
    timestamp("Example #4: Graph w/ Curve + Point")

    # Graph
    g = FirstQuadrant(xRange=(-1, 7))

    wait(0.1)

    # Curve
    f = FunctionGraph(
        f=lambda x: math.cos(x),
        xRange=(0, g.xRange[1]),
        parentGraph=g,
    ).animate()

    # Update Function
    for i in CubicBezier.range(Easing.Linear, 1, 30, duration=1):
        f.update(f=lambda x: math.cos(x * (1 + i / 15)), numPoints=int(100 * (1 + i / 10)))

    wait()

    # Point on Curve + Value
    p = GraphPoint(f).fromTo(x2=math.pi, duration=3)
    p.tipAbove = False

    return Group(g, f, p).waitForOthers(updateContext=True)


def example5():
    """
    Chess animation.
    """
    timestamp("Example #5: Chessboard")

    c = ChessBoard()
    # c.play()
