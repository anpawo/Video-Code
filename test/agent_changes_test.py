#!/usr/bin/env python3
"""
The agent's answer ends on the lines it changed, and each one is a link to it.

Read off a windowless editor: a known diff is turned into its changes, the
changes are written under an answer, and a link is followed — the caret has to
land on the changed line, in the coloured view while the turn waits and in the
plain text once it is taken. No window opens, and no agent runs.

Run directly: `python3 test/agent_changes_test.py`
"""

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")

from helpers import check, needsRenderer, section, summary

if not needsRenderer("the pane is the editor's"):
    summary()
    sys.exit(0)

# a · square.wait(1) → square.wait(2) · b · + new() · c · − gone() · d
ROWS = json.dumps([
    {"kind": "same", "text": "a"},
    {"kind": "del", "text": "square.wait(1)"},
    {"kind": "add", "text": "square.wait(2)"},
    {"kind": "same", "text": "b"},
    {"kind": "add", "text": "    new()"},
    {"kind": "same", "text": "c"},
    {"kind": "del", "text": "gone()"},
    {"kind": "same", "text": "d"},
])

keys = ";".join([
    f"Eval:JSON.stringify(agent.changesOf({ROWS}))",
    "Eval:agent.say('Done.')",
    f"Eval:agent.noteChanges(agent.changesOf({ROWS}))",
    "Eval:agent.log[agent.log.length - 1].body.map((b) => b.kind + '|' + b.text).join('~')",
    "Eval:agent.reveal('line:3:5:9')",
    "Eval:source.cursorLine",
    "Eval:source.diffRows = [{kind: 'same', text: 'x'}]",
    "Eval:agent.reveal('line:3:5:9')",
    "Eval:source.cursorLine",
    "Eval:source.diffRows = []",
])
run = subprocess.run(
    ["./video-code", "--editor", "--check-chrome", "--screenshot", f"/tmp/videocode-agent-{os.getpid()}.png",
     "--file", "docs/by-example/tour.py"],
    env={**os.environ, "VC_KEYS": keys, "VC_SETTLE": "2500", "VC_DOCK_FILE": f"/tmp/videocode-agent-{os.getpid()}.json"},
    capture_output=True, text=True, timeout=180,
)
answers = [json.loads(m)[0] for m in re.findall(r"Probed the expression .*? → (\[.*\])$", run.stdout, re.M)]

# ---------------------------------------------------------------------------
section("a diff becomes one change per run of changed lines")

changes = json.loads(answers[0]) if answers else []
check(f"three runs, three changes (got {len(changes)})", len(changes) == 3)
if len(changes) == 3:
    check(f"a replaced line points at its first new character ({changes[0]})",
          (changes[0]["line"], changes[0]["column"], changes[0]["shown"]) == (2, 13, 3) and changes[0]["text"] == "square.wait(2)")
    check(f"an added line, trimmed ({changes[1]})",
          (changes[1]["line"], changes[1]["column"], changes[1]["shown"]) == (4, 1, 5) and changes[1]["text"] == "new()")
    check(f"a removed line says so, where it was ({changes[2]})",
          (changes[2]["line"], changes[2]["shown"]) == (6, 7) and changes[2]["removed"])

# ---------------------------------------------------------------------------
section("they are written under the answer, as links")

body = answers[3] if len(answers) > 3 else ""
check(f"the answer keeps its words and ends on the changes ({body[:90]}…)",
      body.startswith("text|Done.~changes|") and "[2:13](line:2:13:3)" in body and "removed `gone()`" in body)

# ---------------------------------------------------------------------------
section("a link puts the caret on its line")

check(f"once taken, on the line of the text (caret line {answers[5] if len(answers) > 5 else '?'})",
      len(answers) > 5 and answers[5] == 2)
check(f"while the turn waits, on the line of the coloured view (caret line {answers[8] if len(answers) > 8 else '?'})",
      len(answers) > 8 and answers[8] == 8)

summary()
