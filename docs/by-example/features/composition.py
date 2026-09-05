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

import sys

sys.path.insert(0, "docs/by-example/features")

from videocode import *
from card import card
from videocode.input.interface.Composition import Composition
from videocode.template.effect.core.fadeTo import fadeTo


intro = card(
    "A1 · Composition",
    "deux formes identiques, la même transparence",
    "à droite un Group : le recouvrement compte double",
    "à gauche une Composition : une seule teinte",
)

with shot() as demo:
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

cut(intro, demo)
