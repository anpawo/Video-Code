#!/usr/bin/env python3

"""
A5 — `moveAlong(path)` : parcourir une courbe à vitesse constante.

    ./video-code --file docs/by-example/features/move_along.py --generate move_along.mp4

Les deux flèches suivent la MÊME courbe pendant la même durée. En haut,
`moveAlong` : la marche est mesurée d'abord, donc chaque image est un pas de la
même longueur. En bas, la même courbe parcourue point par point : les points
sont serrés dans les virages et espacés sur les lignes droites, donc la flèche
rampe puis détale. `face=True` la tourne dans le sens de la marche.
"""

import sys

sys.path.insert(0, "docs/by-example/features")

from videocode import *
from card import card


POINTS = [(-6, 1.4), (-5.6, 1.4), (-5.2, 1.3), (-4.6, 0.9), (-4, 0.2), (0, 0.2), (6, 0.2)]

intro = card(
    "A5 · moveAlong(path)",
    "la même courbe, la même durée, deux flèches",
    "en haut : un pas est une LONGUEUR — la vitesse ne change pas",
    "en bas : un pas est un point — elle rampe puis détale",
)

with shot() as demo:
    haut = Curve([(x, y + 1.0) for x, y in POINTS], strokeColor=rgba(120, 120, 140))
    bas = Curve([(x, y - 1.6) for x, y in POINTS], strokeColor=rgba(120, 120, 140))

    vitesse = RightTriangle(width=0.7, height=0.5, fillColor=GREEN_A, strokeColor=WHITE)
    vitesse.moveAlong(haut, duration=2.6, easing=Easing.Linear, face=True)

    # Le parcours « naïf » : un point par étape, chacune de la même DURÉE — ce
    # qu'écrit une boucle à la main. Les `start=` sont explicites parce que
    # deux `moveTo` posés sur le même élément sans rien entre eux partent du
    # même moment : le dernier gagnerait et la flèche filerait droit au bout.
    brut = RightTriangle(width=0.7, height=0.5, fillColor=rgba(240, 180, 90), strokeColor=WHITE)
    dessous = [(x, y - 1.6) for x, y in POINTS]
    brut.position(*dessous[0])
    pas = 2.6 / (len(POINTS) - 1)
    for i, (x, y) in enumerate(dessous[1:]):
        brut.moveTo(x=x, y=y, start=i * pas, duration=pas, easing=Easing.Linear)

    Text(text="moveAlong — vitesse constante", fontSize=0.26, fillColor=GREEN_A).position(-3.4, 2.1)
    Text(text="point par point — rampe puis détale", fontSize=0.26, fillColor=rgba(240, 180, 90)).position(-2.8, -2.6)
    wait(3)

cut(intro, demo)
