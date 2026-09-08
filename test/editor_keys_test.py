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
    seen: dict[str, str] = {}
    for m in re.finditer(r"Probed the expression (.+?) → (.*)$", run.stdout, re.M):
        # The same expression asked twice is two answers, not one: `source.found`
        # before and after a step is the whole point of asking it twice.
        key, n = m[1], 1
        while key in seen:
            n += 1
            key = f"{m[1]}·{n}"
        seen[key] = m[2]
    return seen


section("⌘F finds text in the open file")
seen = probe('Ctrl+F;Text:Circle;Eval:source.found;Return;Eval:source.found;Return;Eval:source.found')
# One key, read twice: the strip lands on the first match after the caret, and
# Enter walks to the next. The count is of the whole file — tour.py writes
# Circle twice — and it must survive the re-colouring that follows a scroll.
check("the strip lands on the first match, of the two in the file",
      seen.get("source.found") == '["1/2"]')
check("and Enter walks to the next", seen.get("source.found·2") == '["2/2"]')
check("and Enter again comes back round", seen.get("source.found·3") == '["1/2"]')

section("the keyboard board keeps the keys it hears")
board = probe('I;Eval:shortcuts.heading();Eval:shortcuts.bullets().length;Eval:keyFree("markIn")',
              panel="shortcuts")
check("a key struck on the board names the action it fires",
      board.get("shortcuts.heading()") == '["Mark in"]')
check("and explains it in at most three lines",
      board.get("shortcuts.bullets().length") in ("[1]", "[2]", "[3]"))
check("and the shell's own shortcuts stand down while it is open",
      board.get('keyFree("markIn")') == "[false]")

section("escape is the one key it lets through")
out = probe('Escape;Eval:shortcuts.visible', panel="shortcuts")
check("escape closes the board", out.get("shortcuts.visible") == "[false]")

if os.path.exists(SHOT):
    os.remove(SHOT)
summary()
