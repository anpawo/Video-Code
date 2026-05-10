#!/usr/bin/env python3


import math
import random


from videocode.template.effect.click import click
from videocode.template.input.Button import Button, RedButton
from videocode.template.input.Arrow import Arrow, Arrow, Cursor
from videocode.template.input.Graph import *
from videocode.template.input.Particles import ParticlesRay
from videocode.template.input.Plane import Plane, SoftPlane
from videocode.template.misc.chess.chessboard import ChessBoard
from videocode import *


def example0():
    examples = [
        example1,
        example2,
        example3,
        example4,
        example5,
        example6,
    ]

    for idx, ex in enumerate(examples):
        elems = ex()
        if idx + 1 == len(examples):
            return
        wait(0.5)
        elems.fadeOut(hide=True)
        wait(0.5)


def example1():
    """
    Basic Inputs
    """
    timestamp("Example #1: All Basic Inputs / Shapes")

    plane = SoftPlane()

    rect = Rectangle(height=2, width=4).position(x=-7)
    circle = Circle(radius=1).position(x=-2)
    sqrRounded = Square(side=2, cornerRadius=30).position(x=1)
    triRandom = Triangle().position(x=4)

    img = Offset(Image("wb.png").position(x=-6.5), x=0, y=0.5)
    text = Text("Hello World", fontSize=0.75).position(x=-5.075)
    triEqui = EquilateralTriangle(side=1).position(x=0)
    triRight = RightTriangle(width=1, height=1).position(x=2)
    triEquiRounded = EquilateralTriangle(side=1, cornerRadius=30).position(x=4)
    arrow = Arrow().position(x=6.5, y=0.5)

    return Group(
        plane,
        Group(rect, sqrRounded, triRandom, circle).align(x=0, y=0).position(y=2),
        Group(text, triEqui, triRight, triEquiRounded).align(x=0, y=0).addInput(img).position(y=0).addInput(arrow),
    ).fadeIn()


def example2():
    """
    Carré qui apparait en grandissant puis qui bouge sur la droite et disparait en grandissant.

    Square that appears by growing, then moves to the right and disappears by growing.
    """
    timestamp("Example #2: Little Square Animation")

    return Group(
        Square(
            fillColor=BLUE_B | 0.9,
            strokeColor=BLUE_A | WHITE,
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

    s = HorizontalLine(length=0, strokeColor=WHITE, fillColor=BLUE_B | 0.5)
    s.ease(s.ref.width, 6).flush()
    s.easeTogether(
        (s.ref.height, 2.5),
        (s.ref.cornerRadius, 15, Easing.Out),
        (s.ref.strokeWidth, 0.05, Easing.Out),
    ).flush()
    s.ease(s.ref.fillColor, BLUE_B | 0.25, easing=Easing.Out).flush()

    wait()

    t = Text("Hello World!").fadeIn()

    return Group(s, t)


def example4():
    """
    First Quadrant of a Cartesian Graph.
    """
    timestamp("Example #4: Graph w/ Curve + Point")

    # Graph
    g = PositiveGraph(xRange=(-1, 7))

    wait(0.1)

    # Curve
    f = FunctionGraph(
        f=lambda x: math.cos(x),
        xRange=(0, g.xRange[1]),
        parentGraph=g,
    ).animate()

    # Update Function
    for i in Easing.Linear.range(1, 30, duration=1):
        f.update(f=lambda x: math.cos(x * (1 + i / 15)), numPoints=int(100 * (1 + i / 10)))

    wait()

    # Point on Curve + Value
    p = GraphPoint(f).fromTo(x2=math.pi, duration=3)
    p.tipAbove = False

    wait(0.3)

    # Wait for others doesnt work
    return Group(g, f, p)


def example5():
    """
    Advanced Animation
    """
    timestamp("Example #5: Advanced Animation")

    p = SoftPlane().fadeIn()

    wait()

    def makeArrows():
        movement = 0.1
        cycles = 5
        circleSize = 1.5

        def makeArrow(deg: float):
            c = math.cos(math.radians(deg)) * circleSize
            s = math.sin(math.radians(deg)) * circleSize
            o = Offset(Arrow(length=0.75, cornerRadius=50), x=-c, y=-s, r=-deg).fadeIn().flush()
            for i in range(cycles):
                sign = 1 if i % 2 == 0 else -1
                o.moveBy(
                    x=c * movement * sign,
                    y=s * movement * sign,
                    duration=0.5,
                    easing=Easing.InOut,
                ).flush()
            return o

        return Group(*[makeArrow(deg) for deg in range(0, 360, 45)])

    arrows = makeArrows()
    button = Button(width=1, height=1, text="Off", color=RED_B).fadeIn().flush()
    cursor = Cursor().position(x=-1, y=-2).align(x=1).fadeIn().flush()

    def buttonHovered(shader: IShader, s: sec, d: sec):
        pos = cast(position, shader)
        assert pos.x is not None
        assert pos.y is not None
        button.isHovered = button.rect.contains(pos.x, pos.y)
        button.waitFor(cursor)
        button.color = button.color

    # What to do when the cursor moves
    cursor.addCallback(position, buttonHovered)

    # Cursor moves to the button
    cursor.moveTo(x=0.35, y=-0.35, duration=0.8).wait(0.1)

    # Button changes to Green when clicked
    button.waitFor(cursor).wait(0.1)
    button.color = GREEN_A
    with button.text:
        button.text.text = "On"
    button.flush()

    # Cursor clicks and Moves out of button
    cursor.apply(*click()).wait(0.05).moveTo(x=2, y=-1, duration=0.8).flush()

    return Group(p, arrows, button, cursor)


def example6():
    """
    Youtube Templates
    """
    timestamp("Example #6: Youtube Templates")

    p = SoftPlane().fadeIn()

    red = Button(width=1, height=1, text="Off", color=RED_B).apply(blur(10)).flush()


# def example5():
#     """
#     Chess animation.
#     """
#     timestamp("Example #5: Chessboard")

#     c = ChessBoard()
#     # c.play()
