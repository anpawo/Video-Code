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

Vérifie dans le lecteur : le fichier a trois chapitres.
"""

from videocode import *

Text(text="C6  ·  timestamp() → chapitres", fontSize=0.34, fillColor=WHITE).position(0, 3.4)

timestamp("l'ouverture")
un = Text(text="l'ouverture", fontSize=0.9, fillColor=WHITE).position(0, 0)
un.fadeIn(duration=0.5)
wait(10.5)

timestamp("le milieu")
un.fadeOut(duration=0.4)
deux = Text(text="le milieu", fontSize=0.9, fillColor=BLUE_C).position(0, 0)
deux.fadeIn(duration=0.5)
wait(10.5)

timestamp("la fin")
deux.fadeOut(duration=0.4)
trois = Text(text="la fin", fontSize=0.9, fillColor=GREEN_A).position(0, 0)
trois.fadeIn(duration=0.5)
wait(10.5)
