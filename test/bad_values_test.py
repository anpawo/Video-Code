#!/usr/bin/env python3
"""
A value a type refuses is reported once, on the line that wrote it, as an
error — whether it came through a verb or a constructor.
"""
import json
import sys

sys.path.insert(0, ".")

import videocode.serialize as serialize  # noqa: E402

SCENE = """from videocode import *

sq = Square(side=1, cornerRadius=200)
sq.opacity(300)
ok = Circle(radius=0.5).opacity(128)
"""

report = serialize.execSource(SCENE, "/tmp/bad_values_scene.py")
assert report["ok"], report
said = json.loads(report["warnings"])
lines = sorted((w["sourceLine"], w["message"], w["severity"]) for w in said)
assert lines == [
    (3, "Square(cornerRadius=200): percent is 0\u2013100", 1),
    (4, "opacity(o=300): uint8 is 0\u2013255", 1),
], lines
assert all(w["input"] >= 0 for w in said), said
print("\033[32m\u2713\033[0m  bad values are refused once, on their line, as errors")
