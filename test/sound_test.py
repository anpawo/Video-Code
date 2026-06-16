#!/usr/bin/env python3

"""
Assertion-based smoke tests for `Sound` (#78, "handle sound") —
verifies the Create-stack entry carries the args the C++ ffmpeg muxing
step (Compiler::generateVideo) needs: filepath, volume, delay, trimStart,
trimEnd.
Run directly: `python3 test/sound_test.py`
"""

import sys

sys.path.insert(0, ".")

from videocode import Sound
from videocode.context import Context

failures: list[str] = []


def check(label: str, condition: bool):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


print("Sound — Create-stack entry")
s = Sound("test/test.wav", start=1.5, volume=0.5, trimStart=0.5, trimEnd=1.5)
entry = Context.stack[s.meta.index][-1]
check("type is Sound", entry["type"] == "Sound")
check("filepath", entry["args"]["filepath"] == "test/test.wav")
check("volume", entry["args"]["volume"] == 0.5)
check("delay (start)", entry["args"]["delay"] == 1.5)
check("trimStart", entry["args"]["trimStart"] == 0.5)
check("trimEnd", entry["args"]["trimEnd"] == 1.5)

print("Sound — defaults")
s2 = Sound("test/test.wav")
entry2 = Context.stack[s2.meta.index][-1]
check("default volume", entry2["args"]["volume"] == 1.0)
check("default delay", entry2["args"]["delay"] == 0)
check("default trimStart", entry2["args"]["trimStart"] == 0)
check("default trimEnd is None", entry2["args"]["trimEnd"] is None)


# ── summary ──────────────────────────────────────────────────────────────────
print()
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All checks passed.")
