#!/usr/bin/env python3
"""
⌘F finds text in the open file, the keyboard board keeps every key it hears, and
two panes may hold the same key while a global one holds it alone.

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
    # A rebinding is persisted the moment it lands — and the file it lands in is
    # the one holding the arrangement a person is working in. VC_DOCK_FILE points
    # that somewhere this test owns.
    env = {**os.environ, "VC_KEYS": keys, "VC_SETTLE": "2500",
           "VC_DOCK_FILE": f"/tmp/videocode-keys-{os.getpid()}.json"}
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
# The caret has to be in the pane first, and which pane opens focused is the
# saved arrangement's business — not this test's.
seen = probe('Eval:showPanel("code");Eval:source.takeFocus();'
             'Ctrl+F;Text:Circle;Eval:source.found;Return;Eval:source.found;Return;Eval:source.found')
# One key, read twice: the strip lands on the first match after the caret, and
# Enter walks to the next. The count is of the whole file — tour.py writes
# Circle twice — and it must survive the re-colouring that follows a scroll.
check("the strip lands on the first match, of the two in the file",
      seen.get("source.found") == '["1/2"]')
check("and Enter walks to the next", seen.get("source.found·2") == '["2/2"]')
check("and Enter again comes back round", seen.get("source.found·3") == '["1/2"]')

section("the keyboard board keeps the keys it hears")
board = probe('I;Eval:keyFree("markIn")', panel="shortcuts")
check("the shell's own shortcuts stand down while it is open",
      board.get('keyFree("markIn")') == "[false]")

section("an action lights while the keys it uses are held")
# The chips are delegates nothing has an id for, so the board's items are walked
# for the lit ones. No `;` in the expression: VC_KEYS splits on it.
LIT = ('(f => f(f, shortcuts))((f, i) => Array.from(i.children).reduce((o, c) => '
       'o.concat(c.lit === true && c.modelData !== undefined && c.modelData.label !== undefined '
       '? [c.modelData.label] : [], f(f, c)), [])).join("|")')
held = probe('Eval:shortcuts.keysStruck = ["Cmd", "R"];Eval:' + LIT, panel="shortcuts")
check("⌘R held lights the one action bound to it", held.get(LIT) == '["Execute the scene"]')

# A scripted key comes back up with its modifiers still set, so letting go of R
# leaves ⌘ down — and a plain key let go leaves nothing.
up = probe('Ctrl+R;Eval:shortcuts.keysStruck.join("|");R;Eval:"" + shortcuts.keysStruck.length',
           panel="shortcuts")
check("letting go of R while ⌘ is down keeps ⌘ lit", up.get('shortcuts.keysStruck.join("|")') == '["Cmd"]')
check("letting go of the only key puts everything out", up.get('"" + shortcuts.keysStruck.length') == '["0"]')
# ⌘ cannot be pressed alone from a script, so its release is asked directly —
# with its flag still on the event, the way some platforms send it.
alone = probe('Eval:"" + shortcuts.heldIn(Qt.ControlModifier, "Cmd").length', panel="shortcuts")
check("letting go of ⌘ puts out what ⌘ lit", list(alone.values()) == ['["0"]'])

section("the two ⌘ keys are two keys")
# The side bits ride on nativeModifiers(), which a synthesised key event does
# not carry — so the rule is asked directly rather than through a keypress.
# The last two are the BINDING case — nothing physically down. A binding is
# written on the left key and shown there: lighting both said "either one",
# which reads as a single key drawn twice.
sides = probe('Eval:"" + shortcuts.sideLit(1, "Cmd", false) + shortcuts.sideLit(1, "Cmd", true)'
              ' + shortcuts.sideLit(2, "Cmd", false) + shortcuts.sideLit(0, "Cmd", false)'
              ' + shortcuts.sideLit(0, "Cmd", true)',
              panel="shortcuts")
check("the ⌘ under your thumb lights, and only that one — and a binding is the left one",
      list(sides.values()) == ['["truefalsefalsetruefalse"]'])

# And it keeps saying so after the key comes back up. Shell.modifierSides is 0
# in a windowless run — the bits ride on nativeModifiers() — so this is exactly
# the "you let go of it" state: reading them live would fall back to the
# binding rule and light the left cap instead of the one that answered.
frozen = probe('Eval:"" + (shortcuts.sidesAt = 1) + shortcuts.sideDown("Cmd", false)'
               ' + shortcuts.sideDown("Cmd", true) + Shell.modifierSides',
               panel="shortcuts")
check("and it still says so once the key is released",
      list(frozen.values()) == ['["1truefalse0"]'])

section("a pane's key is its own, a global key is everyone's")
# Only the code pane has keys of its own today, so the second pane is added to
# the table for the length of the run — the rule is about two panes, and asking
# it with one would be asking nothing.
scope = probe('Eval:Keymap.actions.push({ id: "fake", label: "Fake", where: "Media", scope: "media" })'
              ';Eval:Keymap.holder("Cmd+S", "fake")'
              ';Eval:Keymap.holder("Cmd+S", "markIn")'
              ';Eval:Keymap.holder("F12", "rename")'
              ';Eval:Keymap.holder("Tab", "fake")'
              ';Eval:Keymap.holder("Cmd+/", "fake")'
              ';Eval:Keymap.bind("fake", "Cmd+S")'
              ';Eval:Keymap.combo("save") + "|" + Keymap.combo("fake")'
              ';Eval:Keymap.bind("references", "F12")'
              ';Eval:Keymap.combo("definition") + "|" + Keymap.combo("references")',
              panel="shortcuts")
check("another pane may take the code pane's ⌘S",
      scope.get('Keymap.holder("Cmd+S", "fake")') == '[""]')
check("and it keeps it — the code pane does not lose its own",
      scope.get('Keymap.combo("save") + "|" + Keymap.combo("fake")') == '["Cmd+S|Cmd+S"]')
check("a global key may not take a pane's",
      scope.get('Keymap.holder("Cmd+S", "markIn")') == '["Save the buffer"]')
check("two keys of the same pane still clash",
      scope.get('Keymap.holder("F12", "rename")') == '["Go to definition"]')
check("and the loser is still stripped of it",
      scope.get('Keymap.combo("definition") + "|" + Keymap.combo("references")') == '["|F12"]')
check("Tab belongs to the code pane, so another pane may have it",
      scope.get('Keymap.holder("Tab", "fake")') == '[""]')
check("⌘/ belongs to the menu bar, so nobody may",
      scope.get('Keymap.holder("Cmd+/", "fake")') == '["This board"]')

# And the board itself obeys it: a key is captured by pressing it, so the refusal
# lives in the panel and not only in the table.
taken = probe('Eval:Keymap.actions.push({ id: "fake", label: "Fake", where: "Media", scope: "media" })'
              ';Eval:shortcuts.capturing = "fake"'
              ';Tab'
              ';Eval:Keymap.combo("fake") + "|" + shortcuts.clash'
              ';Eval:shortcuts.capturing = "rename"'
              ';Tab'
              ';Eval:Keymap.combo("rename") + "|" + shortcuts.capturing',
              panel="shortcuts")
check("pressing Tab for another pane's action binds it, and warns of nobody",
      taken.get('Keymap.combo("fake") + "|" + shortcuts.clash') == '["Tab|"]')
check("pressing it for a code action changes nothing — Tab is already that pane's",
      taken.get('Keymap.combo("rename") + "|" + shortcuts.capturing') == '["F2|"]')

section("escape is the one key it lets through")
out = probe('Escape;Eval:shortcuts.visible', panel="shortcuts")
check("escape closes the board", out.get("shortcuts.visible") == "[false]")

for junk in (SHOT, f"/tmp/videocode-keys-{os.getpid()}.json"):
    if os.path.exists(junk):
        os.remove(junk)
summary()
