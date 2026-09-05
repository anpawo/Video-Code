#!/usr/bin/env python3

"""
A1 — `Composition` : un groupe qui se rend comme un seul calque.

    ./video-code --file docs/by-example/features/composition.py --generate composition.mp4

Les deux paires sont identiques et montent à la même transparence. À droite un
`Group` : chaque forme devient transparente pour son compte, donc on voit la
première À TRAVERS la seconde et le recouvrement est plus clair. À gauche une
`Composition` : les deux sont dessinées sur une feuille, et c'est la feuille
qui devient transparente — une seule épaisseur, donc pas de couture.
"""

from videocode import *
from videocode.input.interface.Composition import Composition
from videocode.template.effect.core.fadeTo import fadeTo

titre = Text(text="A1  ·  Composition contre Group", fontSize=0.34, fillColor=WHITE)
titre.position(0, 3.2)

gauche = Composition(
    Circle(radius=1.2, fillColor=WHITE, strokeColor=TRANSPARENT),
    Square(side=1.8, fillColor=WHITE, strokeColor=TRANSPARENT).position(1.3, 0),
)
gauche.position(-3.8, 0.2)
gauche.opacity(0)

droite = Group(
    Circle(radius=1.2, fillColor=WHITE, strokeColor=TRANSPARENT),
    Square(side=1.8, fillColor=WHITE, strokeColor=TRANSPARENT).position(1.3, 0),
)
droite.position(3.0, 0.2)
droite.opacity(0)

Text(text="Composition — une seule teinte", fontSize=0.26, fillColor=WHITE).position(-3.2, -2.2)
Text(text="Group — la couture apparaît", fontSize=0.26, fillColor=rgba(240, 180, 90)).position(3.4, -2.2)

gauche.apply(*fadeTo(gauche, src=0, dst=128, duration=1.2))
droite.apply(*fadeTo(droite, src=0, dst=128, duration=1.2))
wait(3)
