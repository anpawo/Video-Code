#!/usr/bin/env python3
"""
⌘1..4 switch the layout, through the native menu bar.

On macOS those keys live nowhere but in the menu bar, so they are pressed there,
the way AppKit hands a key equivalent to the menu: a windowless editor, `Menu:n`
in VC_KEYS, and the layout read back off its stdout. No window opens.

It caught the menus being nested one level too deep: Qt never attaches a submenu
inside a submenu, so the Layout items did not exist for macOS and every ⌘n fell
through to nobody.

Run directly: `python3 test/editor_menu_test.py`
"""

import os
import re
import subprocess
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")

from helpers import check, needsRenderer, section, summary

if not needsRenderer("the editor is the built binary"):
    summary()
    sys.exit(0)

if sys.platform != "darwin":
    print("  (skipped: the native menu bar is macOS only)")
    summary()
    sys.exit(0)

# ---------------------------------------------------------------------------
section("⌘2, ⌘3, ⌘4, ⌘1 each land on their layout")

keys = "Eval:template;" + ";".join(f"Menu:{n};Eval:template" for n in (2, 3, 4, 1))
run = subprocess.run(
    ["./video-code", "--editor", "--check-chrome", "--screenshot", f"/tmp/videocode-menu-{os.getpid()}.png",
     "--file", "docs/by-example/tour.py"],
    env={**os.environ, "VC_KEYS": keys, "VC_SETTLE": "2500", "VC_DOCK_FILE": f"/tmp/videocode-menu-{os.getpid()}.json"},
    capture_output=True, text=True, timeout=180,
)
taken = re.findall(r"Probed the menu key ⌘(\d) → (\w+)", run.stdout)
layouts = re.findall(r"Probed the expression template → \[\"(\w+)\"\]", run.stdout)

check(f"every key was taken by a menu item (got {taken})", len(taken) == 4 and all(t == "taken" for _, t in taken))
check(f"each key moved to a different layout (got {layouts})", len(layouts) == 5 and len(set(layouts[1:])) == 4)
check("⌘1 comes back to where the run started", layouts[-1:] == layouts[:1])

summary()
