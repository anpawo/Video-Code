#!/usr/bin/env python3

"""
What the scenes ask the renderer to do — counted, not timed.

`bench.py` measures a machine; this measures the WORK. Baking every scene is
pure Python: no GPU, no window, no build, no apt. What it prints is identical
run to run and across PYTHONHASHSEED, so a shared runner can hold it to zero
tolerance where it cannot hold a millisecond to any.

Per scene, never in aggregate: an added scene appends a line and needs no
judgement, while an EXISTING scene that moves is a signal — the same split
`known_failures.txt` already makes for the goldens.

    python3 test/perf/digest.py            # gate
    python3 test/perf/digest.py --update   # accept the new numbers
    python3 test/perf/digest.py --emit bench.json
"""

from __future__ import annotations

import glob
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from videocode.context import Context  # noqa: E402
from videocode.serialize import execScene  # noqa: E402

DIGEST = Path(__file__).parent / "digest.json"

# Scenes whose input does not exist identically off this machine. Excluded by
# name rather than skipped on error: a scene that stops baking must be a
# failure, not a silent shrug.
#   mathtex — its geometry comes out of `latex` and `dvisvgm` AT BAKE TIME, two
#     apt packages nobody pins, and the SVG cache they fill is not committed
#     either. The glyph positions it records are this machine's texlive, not
#     this repository's content.
# That is the criterion, not a list of accidents: a scene whose input does not
# exist identically off this machine. `WebImage(url)` is the general form —
# it downloads at bake time into the gitignored `webimage/`, so any scene using
# one takes its input from the network and can change with no commit behind it.
UNPORTABLE = {
    "test/visual/scenes/mathtex.py",
}

# A glyph outline is FreeType's answer, not this repository's. Left in, a minor
# freetype-py release would move a zero-tolerance golden with no commit behind
# it — 24.6% of the corpus payload is these two keys. Their LENGTH still travels,
# so a scene that stops emitting geometry is still caught.
GEOMETRY = {"points", "contourSizes"}

# Easings run through math.exp/sin/pow, and libm is not required to agree to the
# last bit between platforms. Rounding to 1e-6 is far below any change worth
# gating (the smallest real one measured moved a coordinate by 0.25) and far
# above what a different libm can invent.
PLACES = 6


def normalise(node, key=None):
    if isinstance(node, float):
        value = round(node, PLACES)
        return 0.0 if value == 0 else value  # -0.0 and 0.0 are one number
    if isinstance(node, dict):
        return {k: (len(v) if k in GEOMETRY and isinstance(v, (list, tuple)) else normalise(v, k))
                for k, v in sorted(node.items(), key=lambda kv: str(kv[0]))}
    if isinstance(node, (list, tuple)):
        return [normalise(x) for x in node]
    return node


def scenes() -> list[str]:
    found = sorted(glob.glob("test/visual/scenes/*.py")) + ["eg.py", "test/perf/stress_text.py"]
    return [s for s in found if s not in UNPORTABLE]


def measure() -> dict:
    calls = {"n": 0}
    inner = Context.apply.__func__ if hasattr(Context.apply, "__func__") else Context.apply

    def counted(*args, **kwargs):
        calls["n"] += 1
        return inner(*args, **kwargs)

    Context.apply = staticmethod(counted)

    out: dict[str, dict] = {}
    for scene in scenes():
        calls["n"] = 0
        execScene(scene)
        stack = Context.stack
        shape = json.dumps(normalise(stack), default=str, sort_keys=True)
        out[scene] = {
            "inputs": len(stack),
            "frameSlots": sum(len(v) for v in stack.values()),
            "entries": sum(len(f) for v in stack.values() for f in v.values() if isinstance(f, dict)),
            "applyCalls": calls["n"],
            "events": len(Context.events),
            "lastFrame": Context.lastEverAffectedFrame,
            "shape": hashlib.sha256(shape.encode()).hexdigest()[:16],
        }
    return out


def main() -> int:
    now = measure()

    if "--update" in sys.argv:
        DIGEST.write_text(json.dumps(now, indent=1, sort_keys=True) + "\n")
        print(f"digest written to {DIGEST} ({len(now)} scenes)")
        return 0

    if "--emit" in sys.argv:
        rows = [{"name": "bake/applyCalls", "unit": "count",
                 "value": sum(s["applyCalls"] for s in now.values())},
                {"name": "bake/entries", "unit": "count",
                 "value": sum(s["entries"] for s in now.values())},
                {"name": "bake/inputs", "unit": "count",
                 "value": sum(s["inputs"] for s in now.values())}]
        Path(sys.argv[sys.argv.index("--emit") + 1]).write_text(json.dumps(rows, indent=1) + "\n")
        return 0

    was = json.loads(DIGEST.read_text())
    added = sorted(set(now) - set(was))
    gone = sorted(set(was) - set(now))
    moved = []
    for scene in sorted(set(was) & set(now)):
        for key in ("inputs", "frameSlots", "entries", "applyCalls", "events", "lastFrame", "shape"):
            if was[scene][key] != now[scene][key]:
                moved.append(f"  {scene}  {key}: {was[scene][key]} -> {now[scene][key]}")

    if not moved and not gone:
        for scene in added:
            print(f"new scene, not yet recorded: {scene}")
        print(f"bake digest: {len(set(was) & set(now))} scenes unchanged"
              + (f", {len(added)} new" if added else ""))
        return 1 if added else 0

    if gone:
        print("scenes the digest records but that no longer bake:")
        print("\n".join(f"  {s}" for s in gone))
    if moved:
        print("scenes that ask for different work than the digest records:")
        print("\n".join(moved))
    print("\nIf that is what the change meant, accept it: python3 test/perf/digest.py --update")
    return 1


if __name__ == "__main__":
    sys.exit(main())
