#!/usr/bin/env python3

"""
D6 — `BarChart` / `Leaderboard` : le nombre reste sur sa barre.

    ./video-code --file docs/by-example/features/bar_chart.py --generate bar_chart.mp4

`grow()` écrit chaque valeur avec la MÊME rampe que sa barre : le nombre monte
avec le sommet au lieu de rester où il a été posé. C'est le défaut de tous les
graphiques écrits à la main — le nombre est un texte à une place fixe, et dès
que les barres poussent il se retrouve au milieu de l'une d'elles.

`BarChart.fromCSV("votes.csv", label="parti", value="sièges")` lit les mêmes
données depuis un fichier, et refuse une cellule invalide EN LA SITUANT.
"""

import sys

sys.path.insert(0, "docs/by-example/features")

from videocode import *
from card import card
from videocode.template.input.BarChart import Leaderboard


intro = card(
    "D6 · BarChart et Leaderboard",
    "une barre par ligne de données, triée par valeur",
    "chaque nombre est écrit avec la MÊME rampe que sa barre",
    "il monte donc avec le sommet, au lieu de rester posé",
)

with shot() as demo:
    board = Leaderboard(
        {"Ada": 12, "Grace": 31, "Alan": 22, "Katherine": 27, "Edsger": 18},
        width=9,
        height=3.6,
        color=GREEN_A,
    )
    board.position(0, -0.4)
    board.grow(duration=1.4, every=0.12)
    wait(3)

cut(intro, demo)
