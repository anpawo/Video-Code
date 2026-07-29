#!/usr/bin/env python3

"""
Did this change make the renderer slower?

`bench.py` measures; this one REMEMBERS. It runs the same benchmark, compares
every metric against `test/perf/baseline.json`, and fails when one drifts past
its tolerance — so an optimisation cannot be quietly undone months after the
work that earned it (the history is in docs/optimization.md).

    python3 test/perf/guard.py            # compare (pre-push gate)
    python3 test/perf/guard.py --update   # re-baseline, deliberately

Tolerances are per metric and generous on purpose: a machine under load must
not cry wolf, but a 30% regression is never noise. Timings keep the BEST of
several runs, which is the stable statistic here — the mean drags in whatever
else the laptop was doing.

Re-baselining is a decision, not a chore: run it when a change makes the
renderer legitimately slower (a feature that costs what it is worth) or
legitimately faster (then the new floor protects the win). Say which in the
commit message — `--update` rewrites the record every future run is judged on.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bench import RUNS, SCENE, renderOnce  # noqa: E402 — same directory, same benchmark

BASELINE = Path(__file__).parent / "baseline.json"

# metric -> (how much worse is tolerated, human name)
TOLERANCE = {
    "load": (0.30, "load time (start → first frame)"),
    "msPerFrame": (0.20, "render speed"),
    "total": (0.20, "total wall time"),
    "rssMb": (0.25, "peak memory"),
}


def measure() -> dict:
    best = min((renderOnce() for _ in range(RUNS)), key=lambda r: r["total"])
    return {k: round(best[k], 4) for k in ("load", "msPerFrame", "total", "rssMb")} | {"frames": best["frames"], "scene": SCENE}


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
    for key, (tol, label) in TOLERANCE.items():
        before, after = was[key], now[key]
        drift = (after - before) / before if before else 0.0
        flag = "  ← REGRESSION" if drift > tol else ""
        if flag:
            regressions.append(f"{label}: {before:.2f} → {after:.2f} ({drift:+.0%}, tolerance {tol:+.0%})")
        print(f"{label:<32} {before:>10.2f} {after:>10.2f} {drift:>+8.0%}{flag}")

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
