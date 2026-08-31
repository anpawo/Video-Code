#!/usr/bin/env python3

"""
Did this change make the renderer slower?

`bench.py` measures; this one REMEMBERS. It runs the same benchmark, compares
every metric against `test/perf/baseline.json`, and fails when one drifts past
its tolerance — so an optimisation cannot be quietly undone months after the
work that earned it (the history is in docs/optimization.md).

    python3 test/perf/guard.py            # compare (pre-push gate)
    python3 test/perf/guard.py --record   # compare, and append to history.jsonl
    python3 test/perf/guard.py --update   # re-baseline, deliberately

Not every metric can be a gate
------------------------------
Peak memory is the honest one: measured over 14 runs of a busy machine its
coefficient of variation is 0.86%, so a 5% tolerance means what it says and a
100 MB leak cannot hide under it. Wall time is not: the same statistic on the
same commit swings 2-4% at rest and far more under load, and bootstrapping the
old +-20% gate over those samples fires on 26.8% of clean runs. A gate that
cries wolf one run in four teaches everyone to run it with their eyes closed.

So timings are RECORDED, not gated, except at a margin no amount of load can
reach: twice as slow is never the laptop. What the timings are really for is
`history.jsonl` — one line per measurement, travelling in the commit like a
golden, so the curve outlives the machine that drew it.

Timings keep the BEST of several runs, which is the stable statistic here — the
mean drags in whatever else the laptop was doing.

Re-baselining is a decision, not a chore: run it when a change makes the
renderer legitimately slower (a feature that costs what it is worth) or
legitimately faster (then the new floor protects the win). Say which in the
commit message — `--update` rewrites the record every future run is judged on.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bench import RUNS, SCENE, renderOnce  # noqa: E402 — same directory, same benchmark

BASELINE = Path(__file__).parent / "baseline.json"
HISTORY = Path(__file__).parent / "history.jsonl"

# metric -> (how much worse is tolerated, does it fail the build, human name)
TOLERANCE = {
    "load": (0.30, False, "load time (start → first frame)"),
    "msPerFrame": (1.00, True, "render speed"),
    "total": (0.30, False, "total wall time"),
    "rssMb": (0.05, True, "peak memory"),
}


def measure() -> dict:
    best = min((renderOnce() for _ in range(RUNS)), key=lambda r: r["total"])
    return {k: round(best[k], 4) for k in ("load", "msPerFrame", "total", "rssMb")} | {"frames": best["frames"], "scene": SCENE}


def record(now: dict) -> None:
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    date = subprocess.run(["git", "log", "-1", "--format=%cI"], capture_output=True, text=True).stdout.strip()
    if not sha:
        print("not a git checkout — nothing to attach the measurement to, not recorded")
        return
    # The load average travels with the number, because a measurement taken on
    # a busy machine is not wrong, it is just not comparable. Without it the
    # curve has no way to tell a regression from a compile running alongside.
    row = {"sha": sha, "date": date, "loadavg": round(os.getloadavg()[0], 2)} | now
    # One row per commit, the last measurement winning: `make check` twice on
    # the same commit is a normal thing to do, and two rows for one sha would
    # be indistinguishable from the duplicate a fabricated record produces.
    kept = [ln for ln in HISTORY.read_text().splitlines() if ln.strip() and json.loads(ln).get("sha") != sha] if HISTORY.exists() else []
    HISTORY.write_text("\n".join(kept + [json.dumps(row)]) + "\n")
    print(f"\nrecorded in {HISTORY.name} ({sha[:9]}, load {row['loadavg']}) — commit it, that is the memory")


def main() -> int:
    update = "--update" in sys.argv

    if not BASELINE.exists() and not update:
        print(f"no baseline at {BASELINE} — run `python3 test/perf/guard.py --update` once, on a quiet machine")
        return 1

    now = measure()

    if update:
        BASELINE.write_text(json.dumps(now, indent=2) + "\n")
        print(f"baseline written to {BASELINE}:\n{json.dumps(now, indent=2)}")
        return 0

    was = json.loads(BASELINE.read_text())
    if was.get("scene") != now["scene"] or was.get("frames") != now["frames"]:
        print(f"baseline measured a different workload ({was.get('scene')}, {was.get('frames')} frames) — re-baseline before trusting it")
        return 1

    print(f"{'metric':<32} {'baseline':>10} {'now':>10} {'drift':>9}")
    regressions = []
    for key, (tol, gates, label) in TOLERANCE.items():
        before, after = was[key], now[key]
        drift = (after - before) / before if before else 0.0
        flag = ""
        if drift > tol:
            flag = "  ← REGRESSION" if gates else "  ← slower (recorded, not gated)"
            if gates:
                regressions.append(f"{label}: {before:.2f} → {after:.2f} ({drift:+.0%}, tolerance {tol:+.0%})")
        # Said out loud for the same reason a regression is: a win nobody
        # notices is a win nobody protects, and re-baselining is what turns it
        # into the floor the next change is judged against.
        elif drift < -tol:
            flag = "  ← IMPROVED"
        print(f"{label:<32} {before:>10.2f} {after:>10.2f} {drift:>+8.0%}{flag}")

    if "--record" in sys.argv:
        record(now)

    if not regressions:
        print("\nperformance: within tolerance")
        return 0

    print("\nperformance regressed:")
    for r in regressions:
        print(f"  {r}")
    print("\nIf the cost is deliberate and worth it, re-baseline with `python3 test/perf/guard.py --update`")
    print("and say why in the commit message. If it is not, docs/optimization.md records how the")
    print("current numbers were earned — start there.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
