#!/usr/bin/env python3

"""
D7 — `at=` : dire QUAND en secondes du film.

`start=` compte depuis l'horloge de l'élément — deux secondes après tout ce qui
lui a déjà été écrit. `at=` compte depuis le début du film. C'est `offset=` en
secondes, et rien d'autre.

Ce que ce test tient :
  · `at=t` ouvre à l'image `round(t * FRAMERATE)`, quelle que soit l'horloge ;
  · `at=` et `start=` disent la même chose quand l'horloge est à zéro ;
  · `at=` et `offset=` ensemble sont refusés — deux unités pour une question ;
  · `at=` VERS L'ARRIÈRE est refusé, en nommant S1 : c'est l'écriture antidatée
    dont la valeur de départ est lue à l'exécution de la ligne, pas au moment où
    elle joue.

Run directly: `python3 test/at_seconds_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.template.effect.core.moveTo import moveTo


def frames(i: Input) -> dict[int, dict]:
    return {f: e for f, e in Context.stack[i.meta.index].items() if f != -1}


def opening(i: Input, key: str) -> int:
    """La première image ÉCRITE PAR L'ANIMATION — la pose initiale est à 0."""
    return min(f for f, e in frames(i).items() if key in e and f > 0)


section("at= est offset= en secondes")

# On compare des ENSEMBLES d'images, jamais une constante calculée à la main :
# l'ouverture d'une fenêtre porte une convention (+1) qui appartient au moteur,
# pas à cette fonctionnalité. Ce qui doit être vrai, c'est que les deux mots
# écrivent exactement la même chose.
a = Circle(radius=0.5)
a.position(0, 0)
a.moveTo(x=3, at=2.0, duration=0.4)

a2 = Circle(radius=0.5)
a2.position(0, 0)
a2.apply(*moveTo(a2, x=3, duration=0.4), offset=round(2.0 * FRAMERATE))

check("at=2.0 écrit les mêmes images que offset=60",
      sorted(frames(a)) == sorted(frames(a2)))
check(f"et elles commencent bien à {round(2.0 * FRAMERATE)}",
      min(frames(a)) - round(2.0 * FRAMERATE) in (0, 1))

section("at= et start= coïncident quand l'horloge est à zéro")

b = Circle(radius=0.5)
b.position(0, 0)
b.moveTo(x=3, start=1.0, duration=0.4)
c = Circle(radius=0.5)
c.position(0, 0)
c.moveTo(x=3, at=1.0, duration=0.4)
check("start=1.0 et at=1.0 ouvrent à la même image",
      opening(b, "Position") == opening(c, "Position"))

section("at= vit sur le film, start= sur l'élément")

# L'horloge d'un élément avance quand on ATTEND (`flush`), pas à chaque effet :
# `transformationOffset = lastAffectedFrame`, posé par `wait`/`waitTo`. C'est
# donc après une attente que les deux mots cessent de dire la même chose.
d = Circle(radius=0.5)
d.position(0, 0)
d.wait(1.0)                       # horloge de d : 1 s
d.moveTo(x=2, at=3.0, duration=0.4)

dd = Circle(radius=0.5)
dd.position(0, 0)
dd.wait(1.0)
dd.moveTo(x=2, start=3.0, duration=0.4)

# L'écart entre les deux EST l'horloge : `start=` s'ajoute à elle, `at=` l'ignore.
# Elle vaut 31 et non 30 après `wait(1.0)` — la pose initiale a coûté une image,
# et c'est bien la valeur du moteur qu'on veut vérifier, pas 1 s en principe.
check("l'écart entre start=3.0 et at=3.0 vaut exactement l'horloge de l'élément",
      min(frames(dd)) - min(frames(d)) == dd.meta.transformationOffset)
check(f"at=3.0 ouvre au voisinage de {round(3.0 * FRAMERATE)}, pas de {round(4.0 * FRAMERATE)}",
      min(frames(d)) - round(3.0 * FRAMERATE) in (0, 1))

section("deux façons de dire quand : refusé")

e = Circle(radius=0.5)
e.position(0, 0)
try:
    e.apply(hide().at(start=0), at=1.0, offset=30)
    check("at= + offset= lève une erreur", False)
except TypeError as err:
    check("at= + offset= lève une erreur qui nomme les deux",
          "at=" in str(err) and "offset=" in str(err))

section("at= vers l'arrière : refusé, et S1 est nommé")

f = Circle(radius=0.5)
f.position(0, 0)
f.wait(2.0)                       # horloge de f : 2 s
try:
    f.moveTo(x=2, at=0.5, duration=0.4)
    check("un at= derrière l'horloge lève une erreur", False)
except ValueError as err:
    check("l'erreur nomme S1", "S1" in str(err))
    check("l'erreur donne l'image visée et l'horloge", "frame" in str(err))

summary()
