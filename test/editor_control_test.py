#!/usr/bin/env python3
"""
The editor answers `video-code tell` — the channel an agent drives it with.

A windowless editor is started with `--check-chrome --serve`, and every verb
is sent through the real client, the way the Agent pane or a terminal would:
one JSON line in, one out, exit status on `ok`. No window opens.

Run directly: `python3 test/editor_control_test.py`
"""

import json
import os
import subprocess
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "test")

from helpers import check, needsTool, section, summary

if not needsTool("./video-code", "the editor is the built binary"):
    summary()
    sys.exit(0)

SOCKET = f"/tmp/videocode-test-{os.getpid()}.sock"
SCENE = "docs/by-example/tour.py"
env = {**os.environ, "VC_SOCKET": SOCKET}


def tell(*args: str) -> tuple[bool, dict]:
    run = subprocess.run(["./video-code", "tell", *args], env=env, capture_output=True, text=True, timeout=60)
    try:
        answer = json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        answer = {"ok": False, "error": (run.stdout + run.stderr).strip()[-300:]}
    return run.returncode == 0, answer


section("no editor: tell says so and fails")
ok, answer = tell("state")
check("without an editor the client fails, with exit status 1", not ok)

editor = subprocess.Popen(
    ["./video-code", "--editor", "--check-chrome", "--serve", "--file", SCENE],
    env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
)
try:
    section("the windowless editor comes up and answers")
    deadline = time.time() + 30
    ok, state = False, {}
    while time.time() < deadline and not ok:
        time.sleep(0.5)
        ok, state = tell("state")
    check("state answers within 30 s", ok)
    check("it names the open file", ok and state.get("file", "").endswith("tour.py"))
    check(f"the scene ran ({state.get('elements')} elements, {state.get('duration')} s)", ok and state.get("elements", 0) > 10 and state.get("duration", 0) > 20)
    check("the markers are the scene's timestamps", ok and [m["name"] for m in state.get("markers", [])][:2] == ["the opening", "a composition fades as one"])

    section("seek, by seconds and by marker name")
    ok, answer = tell("seek", "at=2.5")
    check("seek at=2.5 lands on 2.5", ok and abs(answer.get("playhead", 0) - 2.5) < 1e-6)
    ok, answer = tell("seek", "at=the numbers")
    check(f"seek at=<marker> lands on the marker ({answer.get('playhead')})", ok and answer.get("playhead", 0) > 10)
    ok, answer = tell("seek", "at=nowhere")
    check("an unknown marker is refused and the markers are listed", not ok and "the opening" in answer.get("error", ""))
    ok, state = tell("state")
    check("state reports the moved playhead", ok and state.get("playhead", 0) > 10)

    section("select, by line and by name")
    ok, listed = tell("elements")
    circle = next((e for e in listed.get("elements", []) if e.get("cls") == "Circle"), {"line": 0})
    ok, answer = tell("select", f"line={circle['line']}")
    check(f"select line={circle['line']} picks the Circle written there", ok and answer.get("selected", {}).get("cls") == "Circle")
    ok, state = tell("state")
    check("and state shows it selected", ok and state.get("selected") is not None and state["selected"].get("line") == circle["line"])
    ok, answer = tell("select", "line=1")
    check("a line that makes nothing is refused", not ok)

    section("play and pause")
    ok, answer = tell("play")
    check("play starts", ok and answer.get("playing") is True)
    ok, answer = tell("pause")
    check("pause stops", ok and answer.get("playing") is False)

    section("run, say, reveal, brief, a JSON request, an unknown verb")
    ok, state = tell("run")
    check("run re-executes and answers with state", ok and state.get("run", {}).get("state") == "fresh")
    ok, answer = tell("say", "text=hello from a test")
    check("say is accepted", ok)
    ok, answer = tell("reveal", "line=40")
    check("reveal moves the caret", ok and answer.get("caret") == 40)
    ok, answer = tell("reveal", "line=58")
    ok, answer = tell("caret")
    check(f"a comment line after wait(3) plays from where the clock stands ({answer.get('at')} s)", ok and answer.get("makes") == "line 58" and 3.5 < answer.get("at", 0) < 4.5)
    ok, answer = tell("reveal", "line=55")
    ok, answer = tell("caret")
    check(f"the caret on the wait(3) itself plays from the wait's start ({answer.get('at')} s)", ok and 0 < answer.get("at", 0) < 3.5)
    ok, answer = tell("reveal", "line=1")
    ok, answer = tell("caret")
    check("the first line plays from 0", ok and answer.get("at") == 0 and answer.get("makes") == "line 1")
    ok, answer = tell("brief")
    check("brief is the <editor> block the agent gets", ok and answer.get("text", "").startswith("<editor>"))
    ok, answer = tell('{"do": "seek", "at": 1}')
    check("a raw JSON request works too", ok and answer.get("playhead") == 1)
    ok, answer = tell("dance")
    check("an unknown verb lists the known ones", not ok and "seek" in answer.get("error", ""))

    section("verify — the whole loop in one answer")
    sheet = f"/tmp/videocode-verify-{os.getpid()}.png"
    ok, answer = tell("verify", f"out={sheet}")
    check("verify runs the scene and answers", ok and answer.get("run", {}).get("state") == "fresh")
    check("it carries what the scene made", ok and answer.get("elements", 0) > 10)
    check("and what the engine noticed", ok and isinstance(answer.get("run", {}).get("warnings"), list))
    check("the sheet is on disk", ok and answer.get("sheet") == sheet and os.path.exists(sheet))
    # The scene named six moments, so the sheet shows THOSE — not an even
    # spread, which on this scene draws the same picture twice.
    check("laid on the scene's own timestamps, not an even spread",
          ok and [round(x, 2) for x in answer.get("sheetAt", [])]
                 == [round(m["at"], 2) for m in answer.get("markers", [])])
    if os.path.exists(sheet):
        os.remove(sheet)

    section("quit")
    ok, answer = tell("quit")
    check("quit is acknowledged", ok)
    try:
        editor.wait(timeout=10)
        check("and the editor exits", True)
    except subprocess.TimeoutExpired:
        check("and the editor exits", False)
finally:
    if editor.poll() is None:
        editor.kill()
    if os.path.exists(SOCKET):
        os.unlink(SOCKET)

summary()
