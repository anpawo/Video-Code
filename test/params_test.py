#!/usr/bin/env python3
"""
Scene parameters: `param(name, default)` in the scene, `--set key=value` and
`--data rows.csv|json` on the command line, one render per row.

What a batch must never do is render N files quietly wrong: a misspelt --set
key, a cell that is not a number, two rows writing the same file, a key given
twice. Each is refused here, and — for the ones only a run can see — by
`--lint` before a single frame.

Run directly: `python3 test/params_test.py` (`VC_BINARY=./build/video-code` to
drive a fresh build rather than the copy at the root).
"""

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "test")

from helpers import check, needsTool, section, summary

from videocode import BLUE, rgba
from videocode import params
from videocode.params import ParamError, param, plan
from videocode.serialize import lintSource

tmp = tempfile.mkdtemp()


def given(values: dict, typed=(), where="--set") -> None:
    os.environ["VC_PARAMS"] = json.dumps({"values": values, "set": list(typed), "from": where})


def refused(call) -> str:
    try:
        call()
    except ParamError as error:
        return str(error)
    return ""


def write(name: str, text: str) -> str:
    path = os.path.join(tmp, name)
    with open(path, "w") as f:
        f.write(text)
    return path


# ---------------------------------------------------------------------------
section("param() reads the value as its default's type")

os.environ.pop("VC_PARAMS", None)
check("nothing given: the default", param("name", "World") == "World" and param("n", 3) == 3)
given({"name": "Ada", "score": "12", "ratio": "0.5", "on": "yes", "brand": "#ff8800", "big": 7.0})
check("text stays text", param("name", "World") == "Ada")
check('"12" is 12 for an int default', param("score", 0) == 12)
check('"0.5" is 0.5 for a float default', param("ratio", 1.0) == 0.5)
check('"yes" is True for a bool default', param("on", False) is True)
check('"#ff8800" is an rgba for a colour default', param("brand", BLUE) == rgba(255, 136, 0))
check("a JSON 7.0 is 7 for an int default", param("big", 0) == 7)
check("no default: required, read as text", param("score") == "12")

given({"score": "lots"}, where="people.csv, row 3")
said = refused(lambda: param("score", 0))
check(f"a cell that is not a number is refused at its row ({said})",
      said.startswith("people.csv, row 3: score='lots' is not a whole number"))
given({"brand": "orange"})
check("a colour that is not hex is refused", "is not a colour" in refused(lambda: param("brand", BLUE)))
given({})
said = refused(lambda: param("title"))
check(f"a required param nobody gave says what to pass ({said[:40]}…)", "pass --set title=" in said)
os.environ.pop("VC_PARAMS", None)

# ---------------------------------------------------------------------------
section("plan(): one render per row, checked before the first frame")

people = write("people.csv", "﻿name,score,email\nAda,12,a@x\nGrace,,g@x\n")
rows = plan([], people, os.path.join(tmp, "out", "{name}.mp4"))
check("one render per row, named from its column",
      [os.path.basename(r["output"]) for r in rows] == ["Ada.mp4", "Grace.mp4"])
check("the output folder is made", os.path.isdir(os.path.join(tmp, "out")))
check("a byte-order mark is not part of the first column", "name" in json.loads(rows[0]["params"])["values"])
check("an empty cell is a value not given — the default applies",
      "score" not in json.loads(rows[1]["params"])["values"])
check("each render knows its place", rows[1]["note"] == "row 2 of 2")
check("no {column}: a batch is numbered",
      [r["output"] for r in plan([], people, "film.mp4")] == ["film-1.mp4", "film-2.mp4"])
check("a lone --set keeps the path as typed", plan(["name=Bob"], "", "film.mp4")[0]["output"] == "film.mp4")
check("--set fills {name} too", plan(["name=Bob"], "", "{name}.mp4")[0]["output"] == "Bob.mp4")
check("a value is made safe for a filename", plan(["name=a/b c"], "", "{name}.mp4")[0]["output"] == "a-b-c.mp4")
check("a value may hold '='", json.loads(plan(["q=a=b"], "", "o.mp4")[0]["params"])["values"]["q"] == "a=b")
check("--set on top of every row", all(json.loads(r["params"])["values"]["lang"] == "fr"
                                       for r in plan(["lang=fr"], people, "{name}.mp4")))
teams = write("teams.json", '[{"name": "Ada", "score": 12}, {"name": "Bob", "score": 3}]')
check("a .json list of objects is rows too", len(plan([], teams, "{name}.mp4")) == 2)

for why, call, expect in [
    ("a key in --set and in the data", lambda: plan(["name=x"], people, "o.mp4"), "also a column"),
    ("--set given twice", lambda: plan(["a=1", "a=2"], "", "o.mp4"), "given twice"),
    ("--set without =", lambda: plan(["name"], "", "o.mp4"), "key=value"),
    ("a {field} that is no column", lambda: plan([], people, "{nope}.mp4"), "neither a --set key nor a --data column"),
    ("a {field} a row leaves empty", lambda: plan([], people, "{score}.mp4"), "row 2 of people.csv leaves empty"),
    ("two rows writing one file", lambda: plan([], write("dup.csv", "name\nA\nA\n"), "{name}.mp4"), "rows 1 and 2 would both write"),
    ("a header and no rows", lambda: plan([], write("empty.csv", "name\n"), "o.mp4"), "nothing to render"),
    ("a missing file", lambda: plan([], os.path.join(tmp, "none.csv"), "o.mp4"), "cannot read"),
    ("neither csv nor json", lambda: plan([], write("rows.txt", "x"), "o.mp4"), ".csv or a .json"),
]:
    said = refused(call)
    check(f"refused: {why}", expect in said)

# ---------------------------------------------------------------------------
section("--lint runs the scene once per row")

scene = "from videocode import *\nname = param('name', 'World')\nscore = param('score', 0)\nText(f'{name} {score}')\nwait(1)\n"
check("no parameters given: the defaults, and nothing to say", lintSource(scene, "card.py") == ("", 0))
check("rows that read: silent but for the column nobody reads",
      lintSource(scene, "card.py", [], people) == (
          "card.py:1: warning: no param() read the --data column email. [unread-column]\n", 0))
text, code = lintSource(scene, "card.py", [], write("bad.csv", "name,score\nAda,1\nBob,lots\n"))
check(f"a bad cell is an error at the param() line, naming its row ({text.strip()})",
      code == 1 and text.startswith("card.py:3: error: bad.csv, row 2: score='lots'") and text.endswith("[param]\n"))
text, code = lintSource(scene, "card.py", ["nmae=Bob"])
check("a misspelt --set key is an error", code == 1 and "--set nmae: the scene has no param() of that name" in text)
text, code = lintSource(scene, "card.py", ["name=x"], people)
check("a plan that is refused is one error line", code == 1 and text.count("\n") == 1 and "also a column" in text)
check("lint leaves VC_PARAMS as it found it", "VC_PARAMS" not in os.environ)

# ---------------------------------------------------------------------------
binary = os.environ.get("VC_BINARY", "./video-code")
if needsTool(binary, "--set and --data are flags of the renderer"):
    section("the command line")
    card = write("card.py", "from videocode import *\nbrand = param('brand', BLUE)\n"
                            "Rectangle(width=W, height=H, fillColor=brand)\nwait(0.2)\n")
    colours = write("colours.csv", "name,brand\nred,#ff0000\ngreen,#00ff00\n")
    run = subprocess.run([binary, "--file", card, "--generate", os.path.join(tmp, "png", "{name}.png"),
                          "--data", colours, "--for", "square,tiktok"], capture_output=True, text=True)
    made = sorted(os.listdir(os.path.join(tmp, "png"))) if os.path.isdir(os.path.join(tmp, "png")) else []
    check(f"rows × shapes, one file each ({made})", run.returncode == 0 and made == [
        "green-square.png", "green-tiktok.png", "red-square.png", "red-tiktok.png"])
    if made:
        from PIL import Image

        def middle(name: str) -> tuple:
            with Image.open(os.path.join(tmp, "png", name)) as im:
                return im.convert("RGB").getpixel((im.width // 2, im.height // 2))

        check("each row is drawn with its own value",
              middle("red-square.png") == (255, 0, 0) and middle("green-tiktok.png") == (0, 255, 0))
    run = subprocess.run([binary, "--file", card, "--generate", os.path.join(tmp, "x.png"), "--set", "bradn=#ff0000"],
                         capture_output=True, text=True)
    check("a misspelt --set key fails the render", run.returncode == 1 and "--set bradn" in run.stderr)
    run = subprocess.run([binary, "--file", card, "--data", colours], capture_output=True, text=True)
    check("--data without --generate is refused", run.returncode == 1 and "needs --generate" in run.stderr)
    run = subprocess.run([binary, "--lint", "--file", card, "--data", colours], capture_output=True, text=True)
    check(f"--lint --data reaches the rows ({run.stdout.strip()})",
          run.returncode == 0 and "--data column name" in run.stdout)

summary()
