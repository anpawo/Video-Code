#!/usr/bin/env python3


from videocode.videocode import *


def example1(i: Input | None = None):
    """
    Carré qui apparait en grandissant puis qui bouge sur la droite et disparait en grandissant.

    Square that appears by growing, then moves to the right and disappears by growing.
    """
    i = i or Square()
    i.position(x=-2).scale(0.1).scaleTo(1).flush().moveTo(x=2).flush().fadeOut().scaleTo(2)


def example2():
    """
    Ligne qui s'étend sur la longueur puis sur la largeur puis qui devient plus foncé.
    Un peu comme une TV ou un paragraphe de texte dans Pokémon.

    Line that extends in length then in height then becomes darker.
    Similar to a TV turning on or a paragraph of text appearing in Pokémon.
    """
    s = Line(length=0, strokeColor=WHITE).easeTo(6, "width").flush()
    s.easeTo(2.5, "height").easeTo(15, "cornerRadius", easing=Easing.Out).easeBy(2, "strokeWidth", easing=Easing.Out).flush()
    s.easeTo(s.fillColor | 0.5, "fillColor", easing=Easing.Out).flush()
