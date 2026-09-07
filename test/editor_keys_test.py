#!/usr/bin/env python3
"""
⌘F finds text in the open file, and the keyboard board keeps every key it hears.

Both live in the chrome, so both are checked the way the chrome is: a windowless
editor, keys pressed into it, and one QML expression read back off its own
stdout. No window opens.

One thing this cannot see: a synthetic QKeyEvent sent to the window never
reaches Qt's shortcut map, so no `Shortcut` in the chrome ever fires here. The
gate that stands them down while the board is open is therefore checked at the
question they all ask — `keyFree()` — and not at the key.

Run directly: `python3 test/editor_keys_test.py`
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

SCENE = "docs/by-example/tour.py"
SHOT = f"/tmp/videocode-keys-{os.getpid()}.png"


def probe(keys: str, panel: str = "") -> dict[str, str]:
    """Press `keys` into a windowless editor and read back every Eval: in them."""
    env = {**os.environ, "VC_KEYS": keys, "VC_SETTLE": "2500"}
    if panel:
        env["VC_PANEL"] = panel
    run = subprocess.run(
        ["./video-code", "--editor", "--check-chrome", "--screenshot", SHOT, "--file", SCENE],
        env=env, capture_output=True, text=True, timeout=180,
    )
    # `Probed the expression <what> → ["value"]` — a one-element JSON array, so
    # a value with newlines in it survives the single line it is printed on.
    return {m[1]: m[2] for m in re.finditer(r"Probed the expression (.+?) → (.*)$", run.stdout, re.M)}


section("⌘F finds text in the open file")
seen = probe('Ctrl+F;Text:Circle;Eval:source.found;Return;Eval:source.found')
check("the strip opens and lands on a match", seen.get("source.found", "").startswith('["2/2'))
check("the count is the whole file — tour.py writes Circle twice", '2/2' in seen.get("source.found", ""))

section("the keyboard board keeps the keys it hears")
board = probe('I;Eval:shortcuts.said();Eval:keyFree("markIn")', panel="shortcuts")
check("a key struck on the board says what it does", board.get("shortcuts.said()") == '["I → Mark in"]')
check("and the shell's own shortcuts stand down while it is open",
      board.get('keyFree("markIn")') == "[false]")

section("escape is the one key it lets through")
out = probe('Escape;Eval:shortcuts.visible', panel="shortcuts")
check("escape closes the board", out.get("shortcuts.visible") == "[false]")

if os.path.exists(SHOT):
    os.remove(SHOT)
summary()
