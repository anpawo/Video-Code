#!/usr/bin/env python3

"""
Assertion-based tests for `SplitView` — the two-panel layout and its split axis.

The contract worth pinning is that `a`/`b` mean the same thing in both
orientations: every scene in the repo (`video.py`, `docs/by-example/tuto.py`)
is written against `sv.a.left`, `sv.b.cx`, ... and must keep working when the
layout stacks. What changes is where the panels sit, never what they are
called.

Run directly: `python3 test/splitview_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.template.input.SplitView import Panel, SplitView

RATIO = 3 / 5

# ── the split axis ───────────────────────────────────────────────────────────
section("split — AUTO follows the frame, the rest is forced")

# The world is 16x9 here (the tests run at the default resolution), so AUTO
# must resolve to columns. The portrait case is covered by the visual suite,
# which renders test/visual/scenes/split_rows.py at 1080x1920.
check("AUTO resolves to COLUMNS in a landscape world", SplitView().split == Split.COLUMNS)
check("...and is never left as AUTO", SplitView().split in (Split.COLUMNS, Split.ROWS))
check("ROWS can be forced whatever the frame", SplitView(split=Split.ROWS).split == Split.ROWS)
check("COLUMNS can be forced too", SplitView(split=Split.COLUMNS).split == Split.COLUMNS)

# ── geometry ─────────────────────────────────────────────────────────────────
section("columns — a beside b, ratio on the width")

cols = SplitView(ratio=RATIO, split=Split.COLUMNS)
check("a is left of b", cols.a.cx < cols.b.cx)
check("both are vertically centred", cols.a.cy == 0 and cols.b.cy == 0)
check("same height", cols.a.height == cols.b.height)
check("ratio sizes b against a, on the split axis", abs(cols.b.width / cols.a.width - RATIO) < 1e-9)
check("they do not overlap", cols.a.x + cols.a.width / 2 <= cols.b.x - cols.b.width / 2)
check("they stay inside the world", cols.a.x - cols.a.width / 2 >= -WORLD_OFFSET_X
      and cols.b.x + cols.b.width / 2 <= WORLD_OFFSET_X)

section("rows — a above b, ratio on the height")

rows = SplitView(ratio=RATIO, split=Split.ROWS)
check("a is ABOVE b (written first, read first)", rows.a.cy > rows.b.cy)
check("both are horizontally centred", rows.a.cx == 0 and rows.b.cx == 0)
check("same width", rows.a.width == rows.b.width)
check("ratio sizes b against a, on the split axis", abs(rows.b.height / rows.a.height - RATIO) < 1e-9)
check("they do not overlap", rows.b.y + rows.b.height / 2 <= rows.a.y - rows.a.height / 2)
check("they stay inside the world", rows.a.y + rows.a.height / 2 <= WORLD_OFFSET_Y
      and rows.b.y - rows.b.height / 2 >= -WORLD_OFFSET_Y)
check("stacking uses the full width", rows.a.width > cols.a.width)

# ── the API a scene is written against ───────────────────────────────────────
section("panels answer the same questions in both layouts")

for name, sv in (("columns", cols), ("rows", rows)):
    for panel in (sv.a, sv.b):
        check(f"{name}: left < right", panel.left < panel.right)
        check(f"{name}: bot < top", panel.bot < panel.top)
        check(f"{name}: inner box is the panel minus its padding",
              abs(panel.innerWidth - (panel.width - 2 * panel.padding)) < 1e-9
              and abs(panel.innerHeight - (panel.height - 2 * panel.padding)) < 1e-9)
        check(f"{name}: the centre is inside the inner box",
              panel.left < panel.cx < panel.right and panel.bot < panel.cy < panel.top)

check("a panel is a Group, so it can be animated like any Input",
      isinstance(cols.a, Panel) and isinstance(cols.a, Group))

summary()
