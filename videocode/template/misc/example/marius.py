#!/usr/bin/env python3


from videocode.template.input.Graph import *
from videocode.template.misc.chess.chessboard import ChessBoard
from videocode.videocode import *


def example1():
    """
    Simple carré arrondi.

    Simple rounded square.
    """
    x = -1.5
    y = 0

    r = Rectangle(height=2, width=2 * 16 / 9).align(x=1, y=1).position(x - 1, y + 1).flush()
    s = Square(side=2, cornerRadius=30).align(x=1, y=0).position(x - 1, y - 1).flush()
    c = Circle(radius=1).align(x=0, y=1).position(x + 1, y + 1).flush()
    i = Image("wb.png").align(x=0, y=0).position(x + 1, y - 1).scale(1.75).flush()
    t = (
        Group(
            Text("Hello", fontSize=0.75),
            ((0, -1), Text("World!", fontSize=0.75)),
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
    Square(side=2).position(x=-2).scale(0.1).scaleTo(1).flush().moveTo(x=2).flush().fadeOut().scaleTo(2)


def example3():
    """
    Ligne qui s'étend sur la longueur puis sur la largeur puis qui devient plus foncé.
    Un peu comme une TV ou un paragraphe de texte dans Pokémon.

    Line that extends in length then in height then becomes darker.
    Similar to a TV turning on or a paragraph of text appearing in Pokémon.
    """
    s = Line(length=0, strokeColor=WHITE).easeTo(6, "width").flush()
    s.easeTo(2.5, "height").easeTo(15, "cornerRadius", easing=Easing.Out).easeBy(2, "strokeWidth", easing=Easing.Out).flush()
    s.easeTo(s.fillColor | DARK_BLUE | 0.25, "fillColor", easing=Easing.Out).flush()

    wait()

    t = Text("Hello World!")


def example4():
    """
    First Quadrant of a Cartesian Graph.
    """
    graph = FirstQuadrantGraph()


def example5():
    """
    Chess animation.
    """
    c = ChessBoard()
    # c.play()
