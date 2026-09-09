#!/usr/bin/env python3

"""
S1 — la base d'une animation est lue à l'image où elle OUVRE.

    ./video-code --file docs/by-example/features/deferred_base.py --generate deferred_base.mp4

Les trois carrés reçoivent exactement les mêmes trois déplacements, aux mêmes
secondes. Seul l'ORDRE DES LIGNES change : le premier est écrit dans l'ordre du
film, le deuxième à l'envers — la dernière étape en premier — et le troisième
dans le désordre. Ils bougent ensemble.

Avant S1, chaque animation lisait sa valeur de départ au moment où sa ligne
s'exécutait, pas au moment où elle jouait : le deuxième carré partait de la fin
et descendait au lieu de monter, et le troisième partait d'ailleurs encore. La
scène est maintenant rejouée jusqu'à ce que chaque base soit celle de l'image où
l'animation ouvre — le film ne dépend plus de l'ordre dans lequel il a été tapé.
"""

import sys

sys.path.insert(0, "docs/by-example/features")

from videocode import *
from card import card


ÉTAPES = [(-1.4, 0.0), (0.7, 1.0), (2.8, 2.0)]  # (où, à quelle seconde)
DÉPART = -3.5

intro = card(
    "S1 · la base lue à l'ouverture",
    "les trois carrés reçoivent les mêmes trois déplacements",
    "seul l'ordre des LIGNES change : ordre, envers, désordre",
    "ils bougent ensemble — avant, deux sur trois partaient faux",
    code=[
        "carré = Square(side=0.8)",
        "",
        "# la dernière étape écrite en PREMIER :",
        "# sa base est lue à l'image où elle ouvre,",
        "# plus au curseur, déjà rendu à la fin",
        "carré.moveTo(x=2.8, start=2, duration=0.8)",
        "carré.moveTo(x=0.7, start=1, duration=0.8)",
        "carré.moveTo(x=-1.4, start=0, duration=0.8)",
    ],
    seconds=5.2,
)


def étiquette(texte: str, y: float, couleur: rgba) -> None:
    Text(text=texte, fontSize=0.24, fillColor=couleur).align(x=0).position(-6.6, y + 0.55)


with shot() as demo:
    for x, seconde in ÉTAPES:
        repère = Rectangle(width=0.02, height=4.6, fillColor=rgba(70, 76, 92), strokeColor=TRANSPARENT)
        repère.position(x, 0)
        Text(text=f"{seconde:.0f} s", fontSize=0.2, fillColor=rgba(110, 118, 136)).position(x, -2.6)

    # Écrit dans l'ordre du film : le cas qui a toujours marché.
    ordre = Square(side=0.8, fillColor=GREEN_A, strokeColor=WHITE).position(DÉPART, 1.5)
    for x, seconde in ÉTAPES:
        ordre.moveTo(x=x, start=seconde, duration=0.8)
    étiquette("écrit dans l'ordre", 1.5, GREEN_A)

    # Écrit à l'envers : la dernière étape en premier. C'est la ligne du bas qui
    # ouvre en premier dans le film, et c'est elle qui donne sa base à celle du
    # dessus — pas le curseur, qui est déjà à la fin.
    envers = Square(side=0.8, fillColor=rgba(240, 180, 90), strokeColor=WHITE).position(DÉPART, 0.0)
    for x, seconde in reversed(ÉTAPES):
        envers.moveTo(x=x, start=seconde, duration=0.8)
    étiquette("écrit à l'envers", 0.0, rgba(240, 180, 90))

    # Et dans le désordre, comme un storyboard qu'on remplit par le milieu.
    désordre = Square(side=0.8, fillColor=rgba(150, 170, 255), strokeColor=WHITE).position(DÉPART, -1.5)
    for i in (1, 2, 0):
        x, seconde = ÉTAPES[i]
        désordre.moveTo(x=x, start=seconde, duration=0.8)
    étiquette("écrit dans le désordre", -1.5, rgba(150, 170, 255))

    wait(3.4)

cut(intro, demo)
