#!/usr/bin/env python3


import math


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
    x = -1
    y = 0

    plane = Plane()

    r = Rectangle(height=2, width=4).align(x=1, y=1).position(x - 1, y + 1)
    s = Square(side=2, cornerRadius=30).align(x=1, y=0).position(x - 1, y - 1)
    c = Circle(radius=1).align(x=0, y=1).position(x + 1, y + 1)
    i = Image("wb.png").align(x=0, y=0).position(x + 1, y - 1).scale(1.75)
    t = (
        Group(
            Text("Hello", fontSize=0.75),
            Offset(0, -1, Text("World!", fontSize=0.75)),
        )
        .align(x=0, y=1)
        .position(x + 5, y + 2)
    )

    return Group(plane, r, s, c, i, t).fadeIn().waitForOthers(0.5, updateContext=True)


def example2():
    """
    Carré qui apparait en grandissant puis qui bouge sur la droite et disparait en grandissant.

    Square that appears by growing, then moves to the right and disappears by growing.
    """
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
    s = HorizontalLine(length=0, strokeColor=WHITE, fillColor=DARK_BLUE | 0.5).easeTo(6, "width").flush()
    s.easeTo(2.5, "height").easeTo(15, "cornerRadius", easing=Easing.Out).easeTo(0.05, "strokeWidth", easing=Easing.Out).flush()
    s.easeTo(DARK_BLUE | 0.25, "fillColor", easing=Easing.Out).flush()

    wait()

    t = Text("Hello World!").fadeIn()

    return Group(s, t).waitForOthers(updateContext=True)


def example4():
    """
    First Quadrant of a Cartesian Graph.
    """
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
    p = GraphPoint(f).fromTo(x2=4, duration=4)

    wait(0.3)

    p.fromTo(x1=4, x2=2)

    wait()

    return Group(g, f, p).waitForOthers(updateContext=True)


def example5():
    """
    Chess animation.
    """
    c = ChessBoard()
    # c.play()
