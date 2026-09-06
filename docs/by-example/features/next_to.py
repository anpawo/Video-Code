#!/usr/bin/env python3

"""
D1 — `nextTo(other, direction, gap=)` : mettre ceci à côté de cela.

    ./video-code --file docs/by-example/features/next_to.py --generate next_to.mp4

Quatre étiquettes autour d'une forme, une par direction, chacune à 0.3 unité
du BORD — pas du centre : la forme est un rectangle large, et les étiquettes
de gauche et de droite sont pourtant aussi près que celles du haut et du bas.
Puis la forme grandit, et une nouvelle étiquette posée à côté d'elle se place
d'après sa taille DESSINÉE (X6), pas d'après sa géométrie.
"""

import sys

sys.path.insert(0, "docs/by-example/features")

from videocode import *
from card import card

INK = rgba(238, 240, 246)

intro = card(
    "D1 · nextTo(other, direction, gap=)",
    "quatre étiquettes autour d'un rectangle, une par direction",
    "l'écart se mesure au BORD — large ou haut, même distance",
    "la forme grandit : la suivante lit sa taille DESSINÉE",
    code=[
        "boîte = Rectangle(width=5, height=1.6)",
        "",
        "# 0.3 unité entre les deux BORDS, pas entre les centres",
        'Text(text="UP").nextTo(boîte, UP, gap=0.3)',
        'Text(text="RIGHT").nextTo(boîte, RIGHT, gap=0.3)',
        "",
        "# posée après un scaleTo : elle lit la taille dessinée",
        'Text(text="…").nextTo(boîte, DOWN, gap=0.35)',
    ],
    seconds=5.2,
)

with shot() as demo:
    box = Rectangle(width=5, height=1.6, fillColor=BLUE_C, strokeColor=WHITE)
    autour = []
    for name, direction, t in (("UP", UP, 0.3), ("RIGHT", RIGHT, 0.6), ("DOWN", DOWN, 0.9), ("LEFT", LEFT, 1.2)):
        étiquette = Text(text=name, fontSize=0.4, fillColor=INK)
        étiquette.nextTo(box, direction, gap=0.3).opacity(0).fadeIn(start=t, duration=0.3)
        autour.append(étiquette)

    wait(2)

    # Elles s'en vont pendant que la forme grandit : `nextTo` POSE, il ne suit
    # pas — `follow=True` demande S1, et une étiquette laissée là serait avalée
    # par la forme, ce qui se lit comme un défaut plutôt que comme la règle.
    for étiquette in autour:
        étiquette.fadeOut(duration=0.4)
    box.scaleTo(1.6, duration=0.6)
    wait(0.9)

    # Placée APRÈS le scaleTo : elle lit le rectangle tel qu'il est dessiné
    # maintenant, 8 de large, et tombe à côté de son nouveau bord.
    Text(text="lue à la taille dessinée", fontSize=0.32, fillColor=GREEN_A).nextTo(box, DOWN, gap=0.35).fadeIn(duration=0.4)
    wait(2.2)

cut(intro, demo)
