#!/usr/bin/env python3

"""
C6 — les `timestamp()` deviennent les chapitres du fichier.

    ./video-code --file docs/by-example/features/chapters.py --generate chapters.mp4

`timestamp("nom")` était déjà écrit dans les scènes pour se repérer. Le rendu
en fait maintenant des chapitres DANS le conteneur, et imprime la liste à
coller sous la vidéo. Quand cette liste enfreint une des trois règles de
YouTube — premier chapitre ailleurs qu'à 0:00, moins de trois, un de moins de
dix secondes — le rendu le DIT, au lieu de te laisser coller une liste que
YouTube ignore en silence.

Ouvre le fichier dans un lecteur qui affiche les chapitres : il y en a trois.
"""

import sys

sys.path.insert(0, "docs/by-example/features")

from videocode import *
from card import card


timestamp("l'ouverture")

intro = card(
    "C6 · timestamp() → chapitres",
    "trois moments nommés dans la scène",
    "le rendu les écrit comme chapitres DANS le fichier",
    "et imprime la liste à coller sous la vidéo",
)

with shot() as un:
    Text(text="l'ouverture", fontSize=0.9, fillColor=WHITE).position(0, 0).fadeIn(duration=0.5)
    wait(7)

timestamp("le milieu")

with shot() as deux:
    Text(text="le milieu", fontSize=0.9, fillColor=BLUE_C).position(0, 0).fadeIn(duration=0.5)
    wait(10.5)

timestamp("la fin")

with shot() as trois:
    Text(text="la fin", fontSize=0.9, fillColor=GREEN_A).position(0, 0).fadeIn(duration=0.5)
    wait(10.5)

cut(intro, un, deux, trois)
