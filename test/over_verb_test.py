#!/usr/bin/env python3

"""
`over()` anime une VALEUR, et le dit quand on lui donne un verbe.

`rect.over(duration=0.6).fillColor = RED_B` marche parce que `fillColor` est un
champ. La moitié de ce vers quoi on tend la main — `opacity`, `position`,
`scale`, `rotation` — est un VERBE sur `Input`, pas un champ : l'affectation
mourait trente images plus loin dans l'easing sur
`unsupported operand type(s) for -: 'int' and 'method'`, qui ne nomme ni
l'attribut ni la façon de faire.

Run directly: `python3 test/over_verb_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import Group, RED_B, Square
from videocode.serialize import _resetContext

_resetContext()
rect = Square(side=1)

section("un verbe est refusé en nommant le verbe qui marche")
for name, value, expected in (("opacity", 128, "fadeTo"), ("scale", 2, "scaleTo"),
                              ("position", 1, "moveTo"), ("rotation", 90, "rotateTo")):
    try:
        setattr(rect.over(duration=0.5), name, value)
        check(f"over().{name} est refusé", False)
    except TypeError as error:
        said = str(error)
        check(f"over().{name} → {said.split('Write ')[-1][:34]}",
              "is a verb, not a value" in said and expected in said)

section("un groupe répond pareil — ce n'est pas une histoire de groupe")
try:
    setattr(Group(Square(side=1)).over(duration=0.5), "opacity", 128)
    check("un Group refuse aussi", False)
except TypeError as error:
    check("un Group refuse aussi, avec la même phrase", "fadeTo" in str(error))

section("et un vrai champ s'anime toujours")
rect.over(duration=0.5).fillColor = RED_B
check("fillColor passe", True)
rect.over(duration=0.5).strokeWidth = 0.1
check("strokeWidth passe", True)

summary()
