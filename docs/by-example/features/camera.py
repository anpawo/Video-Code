#!/usr/bin/env python3

"""
A2 — la caméra : déplacer et zoomer l'image entière, et ce qui n'y va pas.

    ./video-code --file docs/by-example/features/camera.py --generate camera.mp4

Les carrés sont dans le monde : ils grossissent et glissent avec la caméra. La
légende en bas est `pinToFrame()` : elle est dans le CADRE, donc elle garde sa
taille et sa place — un sous-titre qui zoomerait avec l'image deviendrait
illisible.
"""

import sys

sys.path.insert(0, "docs/by-example/features")

from videocode import *
from card import card


intro = card(
    "A2 · La caméra",
    "elle déplace et zoome l'image entière",
    "une matrice dans l'étage sommet, pas un composite de tout",
    "la légende du bas est épinglée au cadre : elle ne bouge pas",
)

with shot() as demo:
    Square(side=1.2, fillColor=BLUE_C, strokeColor=WHITE).position(0, 0)
    Square(side=0.9, fillColor=RED_B, strokeColor=WHITE).position(2.6, 1.2)
    Square(side=0.9, fillColor=GREEN_A, strokeColor=WHITE).position(-2.6, -1.2)

    epingle = Text(text="pinToFrame — ne bouge pas", fontSize=0.3, fillColor=WHITE)
    epingle.position(-4.6, -3.5)
    epingle.pinToFrame()

    wait(0.6)
    camera.over(duration=1.6).zoom = 2.2
    camera.moveTo(x=1.6, y=0.7, duration=1.6)
    wait(1.4)
    camera.over(duration=1.2).zoom = 1
    camera.moveTo(x=0, y=0, duration=1.2)
    wait(1)

cut(intro, demo)
