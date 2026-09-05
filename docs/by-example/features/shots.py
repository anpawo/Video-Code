#!/usr/bin/env python3

"""
D3 — `shot()` et `cut()` : nommer un plan, le ranger d'une ligne.

    ./video-code --file docs/by-example/features/shots.py --generate shots.mp4

Sans ça, une scène en trois parties est un fichier où tout ce qui apparaît
reste à l'écran jusqu'à la fin, sauf à cacher chaque élément à la main — et une
quatrième partie oblige à revenir sur les trois premières.
"""

import sys

sys.path.insert(0, "docs/by-example/features")

from videocode import *
from card import card


# Les titres sont posés à 0.2 et non à 0 : un texte laissé PILE à l'origine
# dessine ses lettres l'une sur l'autre (défaut X8 — la mise en page est
# calculée puis jetée comme une écriture sans effet). Le correctif est écrit
# sur la branche fix/text-layout et attend un feu vert, parce qu'il déplace
# l'empreinte des scènes de référence.

intro = card(
    "D3 · shot() et cut()",
    "trois plans, chacun dans son bloc",
    "cut(un, deux, trois) : une seule ligne",
    "chaque plan se range à l'image où le suivant s'ouvre",
)

with shot() as un:
    Text(text="premier plan", fontSize=0.9, fillColor=WHITE).position(0, 0.2).fadeIn(duration=0.4)
    Circle(radius=0.8, fillColor=BLUE_C).position(-4, -1.6).fadeIn(duration=0.4)
    wait(1.6)

with shot() as deux:
    Text(text="deuxième plan", fontSize=0.9, fillColor=GREEN_A).position(0, 0.2).fadeIn(duration=0.4)
    Square(side=1.4, fillColor=GREEN_A).position(4, -1.6).fadeIn(duration=0.4)
    wait(1.6)

with shot() as trois:
    Text(text="troisième plan", fontSize=0.9, fillColor=rgba(240, 180, 90)).position(0, 0.2).fadeIn(duration=0.4)
    wait(1.6)

cut(intro, un, deux, trois)
