#!/usr/bin/env python3
"""
A value past what its type allows is written as the nearest one it does.

Typed into the Inspector's opacity row of a windowless editor: -5 becomes 0 on
the element's line, and the bound is said in plain numbers — "0–255", not the
type's name. No window opens.

Run directly: `python3 test/inspector_bounds_test.py`
"""

import json
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, ".")
sys.path.insert(0, "test")

from helpers import check, needsRenderer, section, summary

if not needsRenderer("the field is the chrome's"):
    summary()
    sys.exit(0)

SCENE = "test/timeline_gaps/scene.py"
SOCKET = f"/tmp/videocode-bounds-{os.getpid()}.sock"
log = tempfile.NamedTemporaryFile(suffix=".log", delete=False)
dock = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
dock.close()
env = {**os.environ, "VC_SOCKET": SOCKET, "VC_DOCK_FILE": dock.name}

# Type into the row called `opacity` and press Enter; answers what the field
# reads afterwards. %s is what is typed.
TYPE = ("(function find(item) { if (item.label === 'opacity' && item.kind !== undefined) {"
        " const field = (function f(i) { if (typeof i.selectAll === 'function' && i.readOnly !== undefined) return i ;"
        " for (const c of i.children) { const r = f(c) ; if (r !== null) return r } return null })(item) ;"
        " field.text = '%s' ; field.accepted() ; return field.text }"
        " for (const c of item.children) { const r = find(c) ; if (r !== null) return r } return null })(inspector)")

# What the Inspector's notice says, or "" when it says nothing.
SAID = ("(function find(item) { if (item.act !== undefined && typeof item.show === 'function') return item.visible ? String(item.children[0].text) : '' ;"
        " for (const c of item.children) { const r = find(c) ; if (r !== null) return r } return null })(inspector)")


def tell(*args: str) -> dict:
    run = subprocess.run(["./video-code", "tell", *args], env=env, capture_output=True, text=True, timeout=60)
    try:
        return json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"ok": False}


def probe(expression: str):
    tell("key", f"spec=Eval:{expression}")
    with open(log.name) as out:
        said = out.read()
    answers = [one for one in said.splitlines() if one.startswith("Probed the expression")]
    if not answers:
        raise AssertionError(f"the editor did not answer the probe `{expression}`.\nWhat it said instead:\n{said[-3000:] or '(nothing at all)'}")
    return json.loads(answers[-1][len("Probed the expression ") + len(expression) + 3 :])[0]


editor = subprocess.Popen(["./video-code", "--editor", "--check-chrome", "--serve", "--file", SCENE],
                          env=env, stdout=log, stderr=subprocess.STDOUT)
try:
    deadline = time.time() + 30
    while time.time() < deadline and not tell("state").get("ok"):
        time.sleep(0.5)

    section("out of bounds, in the Inspector")
    probe("app.inspect(liveScene.elements[0])")
    was = probe("source.text").split("\n")[6]
    reads = probe(TYPE % "-5")
    now = probe("source.text").split("\n")[6]
    check(f"-5 typed for an opacity is written as 0 ({now[len(was):]})", reads == "0" and now == was + ".opacity(0)")
    said = probe(SAID)
    check(f"and the bound is said in numbers, without the type's name ({said})", "0–255" in said and "uint8" not in said)

    reads = probe(TYPE % "300")
    now = probe("source.text").split("\n")[6]
    check(f"300 is written as 255 ({now[len(was):]})", reads == "255" and now == was + ".opacity(255)")

    reads = probe(TYPE % "128")
    now = probe("source.text").split("\n")[6]
    check("a value inside the bounds is written as typed", now == was + ".opacity(128)")

    tell("quit")
    editor.wait(timeout=10)
finally:
    if editor.poll() is None:
        editor.kill()
    for path in (SOCKET, log.name, dock.name):
        if os.path.exists(path):
            os.unlink(path)

summary()
