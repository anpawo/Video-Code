#!/usr/bin/env python3


import math


from videocode.template.input.Graph import *
from videocode.template.input.Plane import Plane
from videocode.template.misc.chess.chessboard import ChessBoard
from videocode import *


def example1():
    """
    Basic Inputs
    """
    x = -1
    y = 0

    plane = Plane()

    r = Rectangle(height=2, width=4).align(x=1, y=1).position(x - 1, y + 1).flush()
    s = Square(side=2, cornerRadius=30).align(x=1, y=0).position(x - 1, y - 1).flush()
    c = Circle(radius=1).align(x=0, y=1).position(x + 1, y + 1).flush()
    i = Image("wb.png").align(x=0, y=0).position(x + 1, y - 1).scale(1.75).flush()
    t = (
        Group(
            Text("Hello", fontSize=0.75),
            Offset(0, -1, Text("World!", fontSize=0.75)),
        )
        .align(x=0, y=1)
        .position(x + 5, y + 2)
        .flush()
    )


def example2():
    """
    Carré qui apparait en grandissant puis qui bouge sur la droite et disparait en grandissant.

    Square that appears by growing, then moves to the right and disappears by growing.
    """
    Square(side=2, cornerRadius=30).position(x=-2).scale(0.1).scaleTo(1).flush().moveTo(x=2).flush().fadeOut().scaleTo(2)


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


def example4():
    """
    First Quadrant of a Cartesian Graph.
    """
    # Graph
    g = FirstQuadrant(xRange=(-1, 7))

    wait(0.3)

    # Curve
    f = FunctionGraph(
        f=lambda x: math.cos(x),
        xRange=(0, g.xRange[1]),
        parentGraph=g,
    ).animate()

    # wait(0.3)

    # Point on Curve + Value
    # p = GraphPoint(f).fromTo(x2=5)

    # wait()

    # p.tipAbove = False
    # p.fromTo(x1=5, x2=3)

    # wait(0.3)

    # Update Function
    for i in CubicBezier.range(Easing.Linear, 1, 60, duration=3):
        f.update(f=lambda x: math.cos(x * (1 + i / 15)), numPoints=int(100 * (1 + i / 10)))


def example5():
    """
    Chess animation.
    """
    c = ChessBoard()
    # c.play()
