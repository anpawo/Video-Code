#!/usr/bin/env python3

"""
`BarChart` and `Leaderboard` — the twelve hand-written lines, and the number
that stays on its bar.

The scale is the first thing to hold: a bar means nothing except against
another bar, so the tallest is exactly the height asked for and the rest are
that height times their share. The second is the number. In every chart written
by hand it is a `Text` at a fixed place, and the moment the bars grow it sits
over the middle of one. Here it is written with the same ramp as its bar, and
the proof is frame by frame: at every frame of the growth, the value's y is its
bar's top.

Run directly: `python3 test/barchart_test.py`
"""

import os
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode.constants import FRAMERATE
from videocode.context import Context
from videocode.serialize import _resetContext
from videocode.template.input.BarChart import BarChart, Leaderboard

DATA = {"Rust": 82, "Go": 61, "Python": 55, "C": 38}


def approx(a: float, b: float, eps: float = 1e-6) -> bool:
    return abs(a - b) <= eps


def heights(chart: BarChart) -> list[float]:
    return [bar.height for bar in chart.bars]


# ── The scale ──────────────────────────────────────────────────────────────
section("a bar is only comparable to a bar drawn to the same scale")
_resetContext()
chart = BarChart(DATA, height=4)

check("one bar per row, one label per bar, one value per bar",
      len(chart.bars) == 4 and len(chart.labels) == 4 and len(chart.values) == 4)
check("the tallest bar is exactly the height asked for", approx(heights(chart)[0], 4))
check("the others are their share of it", approx(heights(chart)[1], 4 * 61 / 82) and approx(heights(chart)[3], 4 * 38 / 82))
check("every bar stands on the same baseline",
      all(approx(bar.meta.position.y - bar.height / 2, chart.baseline) for bar in chart.bars))
check("the labels are under the baseline", all(label.meta.position.y < chart.baseline for label in chart.labels))

_resetContext()
half = BarChart({"a": 41}, height=4, top=82)
check("`top` fixes the scale, so two charts can be read against each other", approx(half.bars[0].height, 2))

_resetContext()
for wrong, why in (
    ({}, "no rows at all"),
    ({"a": 0}, "nothing but zero to draw"),
):
    try:
        BarChart(wrong)
        check(f"{why} is refused", False)
    except ValueError as error:
        check(f"{why} is refused, with a reason ({error})", True)

_resetContext()
try:
    BarChart(DATA, width=1, gap=0.5)
    check("bars that cannot fit are refused", False)
except ValueError as error:
    check(f"bars that cannot fit are refused, with the numbers ({error})", True)

# ── The number that follows ────────────────────────────────────────────────
section("the value is written with the same ramp as its bar")
_resetContext()
growing = BarChart({"one": 10, "two": 5}, height=3)
growing.grow(duration=0.5, every=0)

def rises(inp) -> dict[int, float]:
    """How far this input's own position has risen, frame by frame."""
    entry = Context.stack[inp.meta.index]
    y = {frame: shader["args"]["y"]
         for frame, keys in entry.items() if frame != -1
         for name, shader in keys.items()
         if name.startswith("Position") and shader["args"].get("y") is not None}
    first = y[min(y)]
    return {frame: value - first for frame, value in y.items()}


for i, bar in enumerate(growing.bars):
    # A bar grows from its baseline, so its MIDDLE rises half of what its top
    # does. The value rides the top — so if it is written with the same ramp,
    # it rises exactly twice as far as the bar's own position, on every frame.
    # A `Text` is a group of letters with no index of its own, hence the glyph.
    climbed = rises(bar)
    carried = rises(growing.values[i].inputs[0])
    shared = sorted(set(climbed) & set(carried))
    check(f"bar {i} and its value are claimed on the same frames ({len(shared)} of {len(climbed)})",
          len(shared) == len(climbed) and len(shared) > 3)
    check(f"and the number rises exactly twice the bar's middle — the bar's top (bar {i})",
          all(approx(carried[frame], climbed[frame] * 2, 1e-4) for frame in shared))
    check(f"as far as the bar is tall, by the end (bar {i})",
          approx(carried[max(shared)], growing.bars[i].height, 1e-3))

check("the growth lasts as long as it was asked to",
      max(f for f in Context.stack[growing.bars[0].meta.index] if f != -1) <= round(0.5 * FRAMERATE) + 1)

# ── Biggest first ──────────────────────────────────────────────────────────
section("a leaderboard read in the order the data happened to be in is not one")
_resetContext()
board = Leaderboard({"Ada": 12, "Grace": 31, "Alan": 22})
check("the rows are sorted, biggest first", [name for name, _ in board.rows] == ["Grace", "Alan", "Ada"])
check("and the bars follow them", heights(board)[0] > heights(board)[1] > heights(board)[2])

# ── From a file ────────────────────────────────────────────────────────────
section("fromCSV — the same chart, read from a file")
with tempfile.TemporaryDirectory() as folder:
    named = os.path.join(folder, "seats.csv")
    with open(named, "w") as file:
        file.write("party,seats\nreds,12\nblues,31\n")

    _resetContext()
    fromFile = BarChart.fromCSV(named, label="party", value="seats")
    check("columns by name", fromFile.rows == [("reds", 12.0), ("blues", 31.0)])

    plain = os.path.join(folder, "plain.csv")
    with open(plain, "w") as file:
        file.write("reds,12\nblues,31\n")
    _resetContext()
    check("columns by number when there is no header",
          BarChart.fromCSV(plain, label=0, value=1).rows == [("reds", 12.0), ("blues", 31.0)])

    broken = os.path.join(folder, "broken.csv")
    with open(broken, "w") as file:
        file.write("party,seats\nreds,12\nblues,many\n")
    _resetContext()
    try:
        BarChart.fromCSV(broken, label="party", value="seats")
        check("a value that is not a number is refused", False)
    except ValueError as error:
        check(f"a value that is not a number is refused BY LINE ({error})",
              "broken.csv:3" in str(error) and "many" in str(error))

    _resetContext()
    try:
        BarChart.fromCSV(named, label="party", value="votes")
        check("a column that is not there is refused", False)
    except ValueError as error:
        check(f"a column that is not there names the ones that are ({error})", "seats" in str(error))

summary()
