#!/usr/bin/env python3

"""
D7 — `at=` : dire QUAND en secondes du film.

    ./video-code --file docs/by-example/features/at_seconds.py --generate at_seconds.mp4

`start=` compte depuis l'horloge de l'élément : deux secondes après tout ce qui
lui a déjà été écrit. C'est le bon mot quand on écrit un plan dans l'ordre.

`at=` compte depuis le début du film. C'est le bon mot quand l'instant est déjà
décidé ailleurs — une voix off enregistrée, un temps de musique, un chapitre.

Les deux carrés reçoivent la MÊME ligne à un mot près, après la même attente
d'une seconde. Celui du haut part à sept secondes DE FILM ; celui du bas une
seconde après son horloge plus trois, parce que son horloge avait avancé.

Sept et non trois : la carte d'introduction dure jusqu'à l'image 172, soit 5,7 s,
et un `at=` derrière l'horloge est refusé — la première version de cette scène
demandait `at=3.0` et le garde-fou l'a arrêtée, ce qui est très exactement son
travail.

`at=` vers l'ARRIÈRE est refusé, et l'erreur nomme S1 : tant qu'une animation lit
sa valeur de départ au moment où la ligne s'exécute, écrire derrière une ligne
déjà posée donne un film différent selon l'ordre d'écriture.
"""


from videocode import *
from card import card


intro = card(
    "D7 · at=2.5",
    "start= compte depuis l'horloge de l'élément",
    "at= compte depuis le début du film",
    "même ligne, même attente, deux instants",
)

with shot() as demo:
    Text(text="deux façons de dire « à trois secondes »", fontSize=0.28,
         fillColor=rgba(150, 156, 170)).position(0, 2.5)

    haut = Square(side=0.8, fillColor=GREEN_A, strokeColor=WHITE)
    haut.position(-5, 0.9)
    Text(text="at=7.0  ·  l'horloge du film", fontSize=0.3, fillColor=GREEN_A).position(-3.6, 1.7)

    bas = Square(side=0.8, fillColor=rgba(240, 180, 90), strokeColor=WHITE)
    bas.position(-5, -0.9)
    Text(text="start=3.0  ·  l'horloge de l'élément", fontSize=0.3, fillColor=rgba(240, 180, 90)).position(-3.2, -1.8)

    # La même attente pour les deux : c'est elle qui fait diverger les deux mots.
    # L'horloge d'un élément avance quand on ATTEND, pas à chaque effet.
    haut.wait(1.0)
    bas.wait(1.0)

    haut.moveTo(x=5, at=7.0, duration=0.8, easing=Easing.InOut)
    bas.moveTo(x=5, start=3.0, duration=0.8, easing=Easing.InOut)

    wait(5.5)

cut(intro, demo)
