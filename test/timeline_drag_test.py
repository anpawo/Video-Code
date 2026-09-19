#!/usr/bin/env python3
"""
A clip dragged on the timeline is one edit to one line of the scene.

Driven end to end, the way a hand would: a windowless editor (`--check-chrome
--serve`) is sent real presses, moves and releases on the clips of
`test/timeline_drag/scene.py`, and what is asserted is what the gesture LEFT —
the text of the buffer, and the frames the re-run scene gives the element.
The buffer is never saved, so the fixture on disk stays what it is. No window
opens.

Run directly: `python3 test/timeline_drag_test.py`
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

if not needsRenderer("the gesture is the chrome's"):
    summary()
    sys.exit(0)

SCENE = "test/timeline_drag/scene.py"
SOCKET = f"/tmp/videocode-drag-{os.getpid()}.sock"
log = tempfile.NamedTemporaryFile(suffix=".log", delete=False)
dock = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
shot = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
dock.close()
shot.close()
env = {**os.environ, "VC_SOCKET": SOCKET, "VC_DOCK_FILE": dock.name}

# The strip the code pane says things on has no name outside its own file; it
# is the one item in there that can both `offer` and hold an `act`.
SAID = ("(function find(item) { if (typeof item.offer === 'function' && item.act !== undefined) return item.children[0].text ;"
        " for (const c of item.children) { const r = find(c) ; if (r !== null) return r } return null })(source)")


def tell(*args: str) -> dict:
    run = subprocess.run(["./video-code", "tell", *args], env=env, capture_output=True, text=True, timeout=60)
    try:
        return json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"ok": False}


def probe(expression: str):
    """A QML expression, answered on the editor's stdout."""
    tell("key", f"spec=Eval:{expression}")
    with open(log.name) as out:
        answers = [one for one in out.read().splitlines() if one.startswith("Probed the expression")]
    # By length, not by splitting on the arrow: an offer has one of its own.
    return json.loads(answers[-1][len("Probed the expression ") + len(expression) + 3 :])[0]


def lines() -> list[str]:
    return [""] + probe("source.text").split("\n")


def rows() -> dict[str, dict]:
    fps = 30
    return {e["name"]: {**e, "first": round(e["from"] * fps), "end": round(e["to"] * fps)} for e in tell("elements")["elements"]}


def gesture(spec: str) -> None:
    # A frame first. The lanes are laid out when a frame is prepared, and a
    # windowless editor prepares none on its own: after every re-run the new
    # lanes all sit on the first one, and a press lands on whichever is on top.
    tell("screenshot", f"out={shot.name}")
    tell("key", f"spec={spec}")


editor = subprocess.Popen(["./video-code", "--editor", "--check-chrome", "--serve", "--file", SCENE],
                          env=env, stdout=log, stderr=subprocess.STDOUT)
try:
    deadline = time.time() + 30
    while time.time() < deadline and not tell("state").get("ok"):
        time.sleep(0.5)
    tell("screenshot", f"out={shot.name}")

    # Where the lanes are, asked of the panel rather than written down: the
    # dock decides, and the dock changes.
    pps = probe("timeline.pxPerSecond")
    x0 = 700 - probe("timeline.timeAtWindow(700, 700)") * pps
    top = probe("(function () { for (let y = 0; y < 2000; ++y) if (timeline.elementAtWindow(700, y) !== null) return y ; return -1 })()")
    order = list(rows())

    def at(name: str, seconds: float) -> tuple[float, float]:
        return x0 + seconds * pps, top + 32 * order.index(name) + 16

    def drag(name: str, grab: float, by: float, flags: str = "") -> None:
        """Press `grab` seconds into the clip — from its end when negative — and pull."""
        row = rows()[name]
        x, y = at(name, (row["from"] if grab >= 0 else row["to"]) + grab)
        gesture(f"Drag:{x},{y},{x + by * pps},{y}{flags}")

    original = lines()
    before = rows()

    section("the cursor says what the hand will do")
    # A MouseArea claims the arrow from birth, and every pane had one laid over
    # its whole content to take the keyboard: the arrow was all anyone saw, on a
    # clip's edge as on the text. The probe reads the window's own cursor.
    def cursorAt(x: float, y: float) -> int:
        tell("screenshot", f"out={shot.name}")
        tell("key", f"spec=Hover:{x},{y}")
        with open(log.name) as out:
            seen = [one for one in out.read().splitlines() if one.startswith("Probed a hover at") and " cursor " in one]
        return int(seen[-1].rsplit(" cursor ", 1)[1]) if seen else -1

    row = rows()["circle"]
    left, y = at("circle", row["from"])
    right, _ = at("circle", row["to"])
    check("a clip's left edge offers to stretch it", cursorAt(left + 3, y) == 6)
    check("its right edge too", cursorAt(right - 3, y) == 6)
    check("its body is the arrow until it is taken", cursorAt((left + right) / 2, y) == 0)

    section("a click is still a click")
    gesture("Click:%s,%s" % at("circle", 1.5))
    check("it picks the clip", tell("state").get("selected", {}).get("line") == 11)
    x, y = at("circle", 1.5)
    gesture(f"Drag:{x},{y},{x + 1},{y}")
    check("and a hand that trembles by a pixel has not dragged anything", lines() == original)

    section("the body — the element's own clock, as its .wait()")
    drag("title", 1.0, 2.0)
    check("a wait is written in front of the first thing that takes time",
          lines()[7] == 'title = Text("Hello").wait(2).fadeIn()')
    check("once for the five letters the line makes", probe("source.text").count(".wait(") == 4)
    # 60 or 61: a fade is first SEEN the frame after it starts, and a Text that
    # waited lays its letters out one frame further on.
    check("and the re-run scene starts it 60 frames later", 60 <= rows()["title"]["first"] - before["title"]["first"] <= 61)
    check("said in words", probe(SAID) == "title now starts at 2.1s")

    drag("title", 1.0, -0.5)
    check("dragged again, the same wait changes — no second one", lines()[7] == 'title = Text("Hello").wait(1.5).fadeIn()')
    check("15 frames sooner", 45 <= rows()["title"]["first"] - before["title"]["first"] <= 46)

    drag("title", 1.0, -3.0)
    check("back to where it stood, the wait is gone — not `.wait(0)`", lines()[7] == original[7])
    check("and so is the move", rows()["title"]["first"] == before["title"]["first"])

    drag("title", 1.0, 1.5, ",hold")
    held = probe("timeline.heldIn + ' ' + timeline.heldOut + ' ' + timeline.dropAt.toFixed(1)")
    check(f"while it is held the clip follows, and the moment under its edge is stamped ({held})", held == "1.5 1.5 1.5")
    tell("key", "spec=Escape")
    check("Escape drops it", probe("timeline.heldLane") == -1)
    tell("key", "spec=Click:%s,%s" % at("title", 4.0))
    check("and the release writes nothing", lines() == original)

    section("the left edge — the start moves, the end stays")
    drag("square", 0.06, 0.3)
    check("the wait that was there is the one that changes", lines()[9] == "square.wait(1.3).fadeIn()")
    check("and the hide counted from that clock is told the same moment again", lines()[10] == "square.hide(start=1.2)")
    now = rows()["square"]
    check("9 frames later, ending where it ended",
          now["first"] == before["square"]["first"] + 9 and now["end"] == before["square"]["end"])

    drag("title", 0.06, 1.0)
    now = rows()["title"]
    check("an end the film gives needs no compensation — one edit",
          lines()[7] == 'title = Text("Hello").wait(1).fadeIn()' and now["end"] == before["title"]["end"])

    section("the right edge still writes hide(start=…)")
    drag("square", -0.06, -0.5)
    now = rows()["square"]
    check("the hide moved", lines()[10].startswith("square.hide(start=") and lines()[10] != "square.hide(start=1.2)")
    check("the end is on the tenth the edge snapped to, the start stayed",
          now["end"] == 60 and now["first"] == before["square"]["first"] + 9)

    section("placed by a drop — hide(), then show(start=…): the show is what moves")
    drag("dropped", 0.5, 1.0)
    check("one number", lines()[15] == "dropped.show(start=2)")
    check("30 frames", rows()["dropped"]["first"] == before["dropped"]["first"] + 30)

    section("what it refuses, and says")
    settled = lines()
    drag("circle", 1.0, 1.0)
    check("a wait that is a NAME keeps it, and the name's own line is offered",
          lines() == settled and probe(SAID).startswith("PAUSE → 1.5, read on 1 line"))
    drag("circle", 1.0, -0.2)
    check("sooner too", lines() == settled and probe(SAID).startswith("PAUSE → 0.3"))
    drag("still", 1.0, 1.0)
    check("an element nothing starts has nothing to move",
          lines() == settled and probe(SAID).startswith("nothing says when still starts"))
    drag("late", 0.2, -1.5)
    check("more than its wait holds — the wait() above holds the rest",
          lines() == settled and probe(SAID).startswith("nothing but 0.5s of .wait() to give back on line 21"))
    drag("early", 0.2, 1.0)
    check("a wait() above that swallows the move: the word is taken back, and that is said",
          lines() == settled and probe(SAID).startswith("could not move early"))
    probe("moveElement(Object.assign({}, liveScene.elements[0], {file: '/elsewhere/titles.py'}), 1)")
    check("a line another file wrote", lines() == settled and probe(SAID) == "titles.py wrote that line — open it to change it there")
    probe("moveElement(Object.assign({}, liveScene.elements[0], {kind: 'video'}), 1)")
    check("a video's body: its frames would not follow", lines() == settled and "nothing to move but that line" in probe(SAID))

    with open(SCENE) as onDisk:
        check("and the fixture on disk is what it was", onDisk.read().split("\n") == original[1:])

    tell("quit")
    editor.wait(timeout=10)
finally:
    if editor.poll() is None:
        editor.kill()
    for path in (SOCKET, log.name, dock.name, shot.name):
        if os.path.exists(path):
            os.unlink(path)

summary()
