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

# The white line a lit edge draws, and the bar it belongs to, in the window's
# frame: "lineLeft lineRight barLeft barRight".
EDGE = ("(function find(item) { if ((item.edge === 'in' || item.edge === 'out') && item.children.length > 0 && item.children[0].opacity > 0.5) {"
        " const line = item.children[0] ; const bar = item.parent ;"
        " return [line.mapToItem(null, 0, 0).x, line.mapToItem(null, line.width, 0).x, bar.mapToItem(null, 0, 0).x, bar.mapToItem(null, bar.width, 0).x].join(' ') }"
        " for (const c of item.children) { const r = find(c) ; if (r !== null) return r } return null })(timeline)")

# What the code pane lights for a hand on a clip: per line, its number, the
# line as it will read ("" until the clip is held), the columns that change,
# what is said beside it, and whether that is a refusal.
LIT = "JSON.stringify(source.aimed.map((r) => [r.line, r.text, r.from, r.to, r.note, r.refused]))"


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
        said = out.read()
    answers = [one for one in said.splitlines() if one.startswith("Probed the expression")]
    # An unanswered probe used to raise IndexError on the line below, which says
    # nothing about why — and the editor's own output, the one place that does,
    # was being thrown away with the temporary file. Hand it over instead.
    if not answers:
        raise AssertionError(
            f"the editor did not answer the probe `{expression}`.\n"
            f"What it said instead:\n{said[-3000:] or '(nothing at all)'}"
        )
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

    # ⌘ pushes what follows and ⇧ snaps: the two together are the gesture the
    # sections below were written against, and a drag with neither is the
    # default one, checked on its own further down.
    def drag(name: str, grab: float, by: float, flags: str = ",cmd,shift") -> None:
        """Press `grab` seconds into the clip — from its end when negative — and pull."""
        row = rows()[name]
        x, y = at(name, (row["from"] if grab >= 0 else row["to"]) + grab)
        gesture(f"Drag:{x},{y},{x + by * pps},{y}{flags}")

    def aimed() -> list:
        return json.loads(probe(LIT))

    def span(row: list) -> str:
        """The part of a lit line that changes, read off the line as it will be — or as it is."""
        return (row[1] or lines()[row[0]])[row[2]:row[3]]

    original = lines()
    before = rows()

    section("a gap's label is its handle")
    # Pull the label sideways and the gap ends where you let go; click it and it
    # is still the field you type into. A handle on the band's edge would sit
    # over the clips — a gap starts exactly where one ends.
    gaps = json.loads(probe("JSON.stringify(liveScene.waits)"))
    check("the scene has the three gaps this fixture writes", len(gaps) == 3)

    STAMPS = ("JSON.stringify((function(){ const out = {} ; function f(it) { for (const c of it.children) f(c) ; "
              "if (it.text !== undefined && String(it.text).indexOf('wait ') === 0) "
              "{ const p = it.mapToItem(null, it.width / 2, it.height / 2) ; out[String(it.text)] = [p.x, p.y] } } "
              "f(timeline) ; return out })())")

    def stampOf(gap: dict) -> list:
        return json.loads(probe(STAMPS))["wait %.1fs" % gap["d"]]

    def pullStamp(gap: dict, by: float) -> None:
        where = stampOf(gap)
        gesture(f"Drag:{where[0]},{where[1]},{where[0] + by * pps},{where[1]}")

    pulled = gaps[1]

    def gapOn(line: int) -> float:
        """The number the `wait()` on that line now carries."""
        return float(lines()[line].split("(")[1].split(")")[0])

    was = gapOn(pulled["line"])
    pullStamp(pulled, 0.5)
    check(f"pulled right, the gap's own line is longer ({was} → {gapOn(gaps[1]['line'])})",
          gapOn(pulled["line"]) > was)
    check("and it says which line it wrote", probe(SAID).endswith("on line %d" % pulled["line"]))
    while lines() != original:
        probe("source.undo()")
    probe("app.executeScene()")

    # The long gap for this one: shortening a three-tenths gap cannot pass the
    # drag threshold before it reaches zero at this zoom.
    wide = gaps[0]
    long = gapOn(wide["line"])
    pullStamp(wide, -0.5)
    check(f"pulled left, that gap's line is shorter ({long} → {gapOn(wide['line'])})",
          gapOn(wide["line"]) < long)
    while lines() != original:
        probe("source.undo()")
    probe("app.executeScene()")

    where = stampOf(pulled)
    gesture("Click:%s,%s" % (where[0], where[1]))
    opened = probe("timeline.editingWait")
    check(f"a click on the label still opens the field to type in (opened {opened}, wanted {pulled['line']})",
          opened == pulled["line"] and lines() == original)
    gesture("Escape")

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

    section("the edge that lights is the clip's own, and it says what it would write")
    row = rows()["square"]
    left, y = at("square", row["from"])
    right, _ = at("square", row["to"])
    cursorAt(right + 5, y)
    time.sleep(0.3)
    lit = [float(v) for v in probe(EDGE).split()]
    check(f"hovered from just outside, the right edge's line ends on the bar's own edge ({lit})",
          abs(lit[1] - lit[3]) < 0.5 and lit[1] - lit[0] <= 2)
    seen = aimed()
    check(f"hovered, the code pane lights the line a drag would change, and the number on it ({seen})",
          len(seen) == 1 and seen[0][0] == 10 and span(seen[0]) == "1.5" and not seen[0][5])
    cursorAt(left - 5, y)
    time.sleep(0.3)
    lit = [float(v) for v in probe(EDGE).split()]
    check(f"the left edge's line starts on the bar's left edge ({lit})", abs(lit[0] - lit[2]) < 0.5 and lit[1] - lit[0] <= 2)
    seen = aimed()
    check(f"the left edge lights the wait that moves it, and nothing else: its hide keeps the end where it is ({seen})",
          [(row[0], span(row)) for row in seen] == [(9, "1")])
    cursorAt((left + right) / 2, 5)
    check("the light goes when the pointer leaves the edge", aimed() == [])

    section("a click is still a click")
    gesture("Click:%s,%s" % at("circle", 1.5))
    picked = tell("state").get("selected", {}).get("line")
    UNDER = "(function () { const e = timeline.elementAtWindow(%s, %s) ; return e === null ? 'nothing' : e.n + ' line ' + e.line })()"
    check(f"it picks the clip (picked {picked}, and the click landed on {probe(UNDER % at('circle', 1.5))})",
          picked == 11)
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

    drag("title", 1.0, 1.5, ",hold,cmd,shift")
    held = probe("timeline.heldIn + ' ' + timeline.heldOut + ' ' + timeline.dropAt.toFixed(1)")
    check(f"while it is held the clip follows, and the moment under its edge is stamped ({held})", held == "1.5 1.5 1.5")
    seen = aimed()
    check(f"the code pane shows the line as the release would write it ({seen})",
          len(seen) == 1 and seen[0][:2] == [7, 'title = Text("Hello").wait(1.5).fadeIn()'] and span(seen[0]) == ".wait(1.5)")
    check("while nothing is written yet", lines() == original)
    tell("key", "spec=Escape")
    check("Escape drops it", probe("timeline.heldLane") == -1)
    check("and the light with it", aimed() == [])
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
    settled = lines()
    drag("square", -0.06, -0.5, ",hold,cmd,shift")
    seen = aimed()
    check("held, the buffer is untouched", lines() == settled)
    tell("key", "spec=Escape")
    tell("key", "spec=Click:%s,%s" % at("title", 4.0))
    drag("square", -0.06, -0.5)
    check(f"what the code pane showed is what the release wrote ({seen})",
          len(seen) == 1 and seen[0][:2] == [10, lines()[10]] and span(seen[0]) == lines()[10][len("square.hide(start="):-1])
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
    drag("still", 1.0, 1.0, ",hold,cmd,shift")
    seen = aimed()
    check(f"a refusal is said on the element's line before the button is let go ({seen})",
          len(seen) == 1 and seen[0][5] and seen[0][4].startswith("nothing says when still starts") and lines() == settled)
    tell("key", "spec=Escape")
    tell("key", "spec=Click:%s,%s" % at("title", 4.0))
    drag("still", 1.0, 1.0)
    check("an element nothing starts has nothing to move",
          lines() == settled and probe(SAID).startswith("nothing says when still starts"))
    drag("late", 0.05, -1.5)  # 0.05, not 0.2: a gap's label sits over that lane
    check("more than its wait holds — the wait() above holds the rest",
          lines() == settled and probe(SAID).startswith("nothing but 0.5s of .wait() to give back on line 21"))
    drag("early", 0.2, 1.0)
    check("a wait() above that swallows the move: the word is taken back, and that is said",
          lines() == settled and probe(SAID).startswith("could not move early"))
    probe("moveElement(Object.assign({}, liveScene.elements[0], {file: '/elsewhere/titles.py'}), 1)")
    check("a line another file wrote", lines() == settled and probe(SAID) == "titles.py wrote that line — open it to change it there")
    probe("moveElement(Object.assign({}, liveScene.elements[0], {kind: 'video'}), 1)")
    check("a video's body: its frames would not follow", lines() == settled and "nothing to move but that line" in probe(SAID))

    section("alone — without ⌘, the gap after the clip gives the time back")
    # A gap starts when the last thing before it has ended. `title` ends well
    # before `wait(2)` starts, so it has slack: a small move pushes nothing. A
    # long one makes it the last to end — the wait starts later, and everything
    # under the wait with it. Alone, the wait is shortened by what that cost.
    while lines() != original:
        probe("source.undo()")
    probe("app.executeScene()")
    start = rows()
    after = ("early", "late")

    drag("title", 1.0, 1.0, "")
    now = rows()
    check(f"within its slack, the clip's line is the only one that changes ({lines()[7]})",
          lines()[7] != original[7] and lines()[18] == original[18] and all(now[n]["first"] == start[n]["first"] for n in after))
    probe("source.undo()")
    probe("app.executeScene()")

    drag("title", 1.0, 3.0, ",hold")
    seen = aimed()
    check(f"held past its slack, both lines that will change are lit: the clip's, and the gap's ({seen})",
          [row[0] for row in seen] == [7, 18] and span(seen[1]) == "2")
    tell("key", "spec=Escape")
    tell("key", "spec=Click:%s,%s" % at("title", 4.0))

    drag("title", 1.0, 3.0, "")
    now = rows()
    check(f"released, the clip moved ({lines()[7]})", 88 <= now["title"]["first"] - start["title"]["first"] <= 92)
    check(f"the gap after it is shorter by what the move cost ({lines()[18]})", 0 < gapOn(18) < 2)
    check("and nothing after that gap moved", all(now[n]["first"] == start[n]["first"] for n in after))
    probe("source.undo()")
    check("one ⌘Z takes both lines back", lines() == original)
    probe("app.executeScene()")

    drag("title", 1.0, 3.0, ",cmd")
    now = rows()
    check("with ⌘ the same drag leaves the gap as written, and what follows goes with it",
          lines()[18] == original[18] and all(now[n]["first"] > start[n]["first"] for n in after))
    probe("source.undo()")
    probe("app.executeScene()")

    drag("title", 1.0, 8.0, ",hold")
    held = probe("timeline.heldIn")
    check(f"alone, the clip stops where the gap has nothing left to give (held at {held}s of the 8 pulled)", 4.0 <= held <= 4.3)
    tell("key", "spec=Escape")
    tell("key", "spec=Click:%s,%s" % at("title", 4.0))
    drag("title", 1.0, 8.0, "")
    now = rows()
    check(f"released there, the gap is spent and what follows has not moved ({lines()[7]} · {lines()[18]})",
          gapOn(18) < 0.1 and all(now[n]["first"] == start[n]["first"] for n in after))
    while lines() != original:
        probe("source.undo()")
    probe("app.executeScene()")

    section("nothing snaps unless ⇧ is held")
    drag("title", 1.0, 0.47, ",cmd")
    check(f"free, the wait is the distance the hand went ({lines()[7]})", lines()[7] == 'title = Text("Hello").wait(0.47).fadeIn()')
    probe("source.undo()")
    probe("app.executeScene()")
    drag("title", 1.0, 0.47, ",cmd,shift")
    check(f"with ⇧ it goes to the tenth ({lines()[7]})", lines()[7] == 'title = Text("Hello").wait(0.5).fadeIn()')
    probe("source.undo()")
    probe("app.executeScene()")

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
