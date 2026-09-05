#!/usr/bin/env python3

"""
A5 — `moveAlong(path)` : parcourir une courbe à vitesse constante.

    ./video-code --file docs/by-example/features/move_along.py --generate move_along.mp4

Les deux flèches suivent la MÊME courbe pendant la même durée. En haut,
`moveAlong` : la marche est mesurée d'abord, donc chaque image est un pas de la
même longueur et la vitesse ne change pas dans les virages. En bas, la même
courbe parcourue point par point : les points sont serrés dans les virages et
espacés sur les lignes droites, donc la flèche rampe puis détale.

`face=True` la tourne dans le sens de la marche.
"""

from videocode import *

Text(text="A5  ·  moveAlong — un pas est une longueur, pas un point", fontSize=0.32, fillColor=WHITE).position(0, 3.4)

# Une courbe dont les points sont volontairement mal répartis : serrés à
# gauche, très espacés à droite.
POINTS = [(-6, 1.4), (-5.6, 1.4), (-5.2, 1.3), (-4.6, 0.9), (-4, 0.2), (0, 0.2), (6, 0.2)]

haut = Curve([(x, y + 1.0) for x, y in POINTS], strokeColor=rgba(120, 120, 140))
bas = Curve([(x, y - 1.6) for x, y in POINTS], strokeColor=rgba(120, 120, 140))

vitesse = RightTriangle(width=0.7, height=0.5, fillColor=GREEN_A, strokeColor=WHITE)
vitesse.moveAlong(haut, duration=2.6, easing=Easing.Linear, face=True)

# Le parcours « naïf » : un point par image, ce que fait une boucle écrite à la
# main. Même durée, même courbe.
brut = RightTriangle(width=0.7, height=0.5, fillColor=rgba(240, 180, 90), strokeColor=WHITE)
brut.position(*[(x, y - 1.6) for x, y in POINTS][0])
pas = 2.6 / len(POINTS)
for x, y in [(x, y - 1.6) for x, y in POINTS][1:]:
    brut.moveTo(x=x, y=y, duration=pas, easing=Easing.Linear)

Text(text="moveAlong — vitesse constante", fontSize=0.26, fillColor=GREEN_A).position(-3.4, 2.1)
Text(text="point par point — rampe puis détale", fontSize=0.26, fillColor=rgba(240, 180, 90)).position(-2.8, -2.6)
wait(3)
