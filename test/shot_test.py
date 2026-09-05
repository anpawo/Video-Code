#!/usr/bin/env python3

"""
`shot()` and `cut()` — naming a stretch of the film, and leaving it.

A scene of several sections is written today as one long file in which every
element of every section stays on screen for the rest of the film unless it is
hidden by hand. A shot is the block; `cut` is the one line that puts the whole
of it away, exactly where the next one opens.

What has to hold: the elements of a shot stop being on screen at the frame the
next shot begins — not at the end of the file, and not one frame either side —
and a shot nobody cuts from changes nothing at all.

Run directly: `python3 test/shot_test.py`
"""

import json
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import BLUE_C, Circle, Square, WHITE, wait
from videocode.context import Context, cut, shot
from videocode.serialize import _resetContext, execSource


def model(source: str) -> dict:
    answer = execSource("from videocode import *\n" + source, "shot_test.py")
    if not answer["ok"]:
        raise AssertionError(answer["message"])
    return json.loads(answer["scene"])


def spans(source: str) -> list[tuple[str, int, int]]:
    return [(one["kind"], one["first"], one["last"]) for one in model(source)["elements"]]


# ── What the block collects, and what the cut writes ───────────────────────
# Called directly rather than through a scene, so what is being tested is the
# two verbs and not the way a file is executed.
section("the block collects what was made in it")
_resetContext()
with shot() as first:
    early = Square(side=1)
    early.fadeIn()
    wait(1)

with shot() as second:
    late = Circle(radius=1)
    late.fadeIn()
    wait(1)

check("each block holds what its lines made", first.inputs == [early] and second.inputs == [late])
check(f"and knows where it opened ({first.first} then {second.first})", first.first == 0 and second.first > first.first)

cut(first, second)
hidden = [frame for frame, keys in Context.stack[early.meta.index].items()
          if frame != -1 and any(key.startswith("Hide") for key in keys)]
check(f"cut writes one Hide on the first shot's element, at the second's opening frame ({hidden})",
      hidden == [second.first])
# The second's element carries a Hide of its own at frame 0 — every element
# born mid-timeline hides itself back to the start of the scene — and that one
# is not a cut. What matters is that nothing hides it once it is on screen.
after = [frame for frame, keys in Context.stack[late.meta.index].items()
         if frame != -1 and frame >= second.first and any(key.startswith("Hide") for key in keys)]
check(f"and nothing hides the second's, once it is on screen ({after})", after == [])

_resetContext()

# ── A cut is where one shot stops being on screen ──────────────────────────
section("cut() ends a shot where the next one opens")
TWO = """
with shot() as intro:
    title = Square(side=1)
    title.fadeIn()
    wait(1)

with shot() as body:
    other = Circle(radius=1)
    other.fadeIn()
    wait(1)

cut(intro, body)
"""
made = spans(TWO)
check(f"both shots are on the timeline ({len(made)} elements)", len(made) == 2)

square, circle = made
check(f"the second shot opens where the first was left ({circle[1]})", circle[1] > square[1])
check(f"and the first stops one frame before it ({square[2]} then {circle[1]})", square[2] == circle[1] - 2 or square[2] == circle[1] - 1)
check("the second runs to the end of the scene", circle[2] >= square[2])

section("a shot nobody cuts from changes nothing")
kept = spans(TWO.replace("cut(intro, body)", ""))
check("its element is still there at the end", kept[0][2] > made[0][2] and kept[0][2] == kept[1][2])

# ── Three in a row ─────────────────────────────────────────────────────────
section("cut(a, b, c) — each one closes the one before it")
THREE = """
with shot() as a:
    Square(side=1).fadeIn()
    wait(1)

with shot() as b:
    Circle(radius=1).fadeIn()
    wait(1)

with shot() as c:
    Square(side=2).fadeIn()
    wait(1)

cut(a, b, c)
"""
one, two, three = spans(THREE)
check(f"the first ends where the second opens ({one[2]} → {two[1]})", one[2] < two[1])
check(f"the second ends where the third opens ({two[2]} → {three[1]})", two[2] < three[1])
check("only the last one is still there at the end", three[2] > two[2] > one[2])

# ── Nesting ────────────────────────────────────────────────────────────────
section("a shot inside a shot is part of it")
NESTED = """
with shot() as outer:
    Square(side=1).fadeIn()
    with shot() as inner:
        Circle(radius=1).fadeIn()
    wait(1)

with shot() as after:
    Square(side=2).fadeIn()
    wait(1)

cut(outer, after)
"""
outerSquare, innerCircle, lastSquare = spans(NESTED)
check("the element made inside the inner shot is cut with the outer one",
      innerCircle[2] < lastSquare[2] and innerCircle[2] == outerSquare[2])

# ── What it refuses ────────────────────────────────────────────────────────
section("what cut() refuses")
answer = execSource("from videocode import *\nwith shot() as only:\n    pass\ncut(only)\n", "shot_test.py")
check(f"a single shot is refused, with a reason ({answer['message']})",
      not answer["ok"] and "two shots" in answer["message"])

# ── Le fondu enchaîné ──────────────────────────────────────────────────────
section("cut(crossfade=…) — les deux plans se traversent, chacun d'un seul bloc")
_resetContext()
with shot() as before:
    Square(side=2.4, fillColor=WHITE).position(-3, 0)
    wait(1)

with shot() as after:
    Circle(radius=1.3, fillColor=BLUE_C).position(3, 0)
    wait(1.5)

cut(before, after, crossfade=0.6)

# Un plan qui se dissout devient UN calque : sans ça, deux plans qui fondent
# membre par membre se voient à travers les trous l'un de l'autre.
check("le plan sortant est devenu un calque", before._layer is not None)
check("le plan entrant aussi", after._layer is not None)
check("et asOneLayer() rend le même, pas un deuxième", before.asOneLayer() is before._layer)


def levels(layer) -> list[tuple[int, float]]:
    entry = Context.stack[layer.layer.meta.index]
    return sorted((frame, shader["args"]["opacity"])
                  for frame, keys in entry.items() if frame != -1
                  for name, shader in keys.items() if name.startswith("Opacity"))


going, coming = levels(before._layer), levels(after._layer)
# La première image de la rampe vaut déjà un cran en dessous : une
# revendication qui redit 255 à un calque déjà à 255 est jetée comme une
# écriture sans effet, et c'est la bonne règle.
check(f"le sortant descend jusqu'à 0 ({going[0][1]:.0f} → {going[-1][1]:.0f})",
      going[0][1] > 200 and going[-1][1] < 15
      and all(a[1] >= b[1] for a, b in zip(going, going[1:])))
check(f"l'entrant monte de 0 à 255 ({coming[0][1]:.0f} → {coming[-1][1]:.0f})",
      coming[0][1] < 15 and coming[-1][1] > 240)
check(f"sur la même fenêtre, qui s'ouvre à la coupe (image {coming[0][0]} pour une coupe à {after.first})",
      abs(coming[0][0] - after.first) <= 1 and abs(going[-1][0] - coming[-1][0]) <= 1)
check(f"et elle dure ce qui a été demandé ({going[-1][0] - going[0][0] + 1} images pour 0.6 s)",
      abs((going[-1][0] - going[0][0] + 1) - 18) <= 2)

hidden = [frame for frame, keys in Context.stack[before._layer.layer.meta.index].items()
          if frame != -1 and any(key.startswith("Hide") for key in keys)]
check(f"le calque sortant est éteint à la fin du fondu ({hidden})",
      len(hidden) == 1 and hidden[0] >= going[-1][0])

_resetContext()
answer = execSource("from videocode import *\nwith shot() as a:\n    pass\nwith shot() as b:\n    pass\ncut(a, b, crossfade=-1)\n", "shot_test.py")
check(f"un fondu de durée négative est refusé ({answer['message']})",
      not answer["ok"] and "crossfade" in answer["message"])

summary()
