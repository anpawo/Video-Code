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
    # +100% was the price of a gate that judged whatever machine it found. Now
    # that it declines to judge an unfit one, the tolerance only has to cover
    # the spread between two FIT readings — measured on 2026-09-01 at 40%
    # (6.02 ms and 8.42 ms, both at a load average under 3, same commit). 50%
    # leaves room above that and is half of what it was.
    #
    # It cannot go much lower while the benchmark scene is this light: measured
    # the same day, one rectangle costs 6.4 ms/frame and 47 animated letters
    # 8.6, so most of what is being gated is a constant that has nothing to do
    # with what is drawn. A scene dominated by rendering work would move ~2.7x
    # above that floor and could be held far tighter.
    "msPerFrame": (0.50, True, "render speed"),
    "total": (0.30, False, "total wall time"),
    "rssMb": (0.05, True, "peak memory"),
}


# How far the RUNS may disagree with each other before the machine is judged
# unfit to be measured on. It is the only signal available from inside a single
# measurement, and it is a floor rather than a proof: three runs that agree can
# still all be slow together, which is how the 9.08 baseline came to be 50%
# above what this machine does when it is quiet. What it does catch is the
# other half — measured on 2026-09-01, the same scene and the same commit gave
# runs 2% apart at one moment and 104% apart an hour later.
STEADY = 0.15

# And a ceiling on the machine itself. The load average does NOT predict the
# fine differences — measured on 2026-09-01, the slowest reading of the day came
# on the quietest machine of the day — so it is no use as a correction. What it
# does say without ambiguity is when a machine has no business being baselined
# at all: at load 10.5 the three runs agreed within 4% and wrote a baseline of
# 8.87 ms, on a machine that does 6.0 when it is quiet. Three runs agreeing only
# means they were slow together.
CALM = 4.0


def measure() -> dict:
    runs = [renderOnce() for _ in range(RUNS)]
    best = min(runs, key=lambda r: r["total"])
    speeds = [r["msPerFrame"] for r in runs]
    spread = (max(speeds) - min(speeds)) / min(speeds) if min(speeds) else 0.0
    return (
        {k: round(best[k], 4) for k in ("load", "msPerFrame", "total", "rssMb")}
        | {"frames": best["frames"], "scene": SCENE}
        # Kept with the number, like the load average: it is what says whether
        # the number deserves to be believed.
        | {"spread": round(spread, 4), "loadavg": round(os.getloadavg()[0], 2)}
    )


def unfit(now: dict) -> str:
    """Why this measurement must not become a baseline, or "" if it may.

    Two coarse filters, neither claiming precision. Jitter is what the runs
    disagreeing catches; a machine that is merely slow throughout is what the
    load ceiling catches. Neither can catch the other, which is the whole
    reason there are two.
    """
    if now["spread"] > STEADY:
        return f"the {RUNS} runs disagreed by {now['spread']:.0%}"
    if now["loadavg"] > CALM:
        return f"the load average is {now['loadavg']}, and {CALM} is the ceiling"
    return ""


def record(now: dict) -> None:
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    date = subprocess.run(["git", "log", "-1", "--format=%cI"], capture_output=True, text=True).stdout.strip()
    if not sha:
        print("not a git checkout — nothing to attach the measurement to, not recorded")
        return
    # The load average travels with the number, because a measurement taken on
    # a busy machine is not wrong, it is just not comparable. Without it the
    # curve has no way to tell a regression from a compile running alongside.
    row = {"sha": sha, "date": date, "loadavg": now.get("loadavg", round(os.getloadavg()[0], 2))} | now
    # One row per commit, the last measurement winning: `make check` twice on
    # the same commit is a normal thing to do, and two rows for one sha would
    # be indistinguishable from the duplicate a fabricated record produces.
    kept = [ln for ln in HISTORY.read_text().splitlines() if ln.strip() and json.loads(ln).get("sha") != sha] if HISTORY.exists() else []
    HISTORY.write_text("\n".join(kept + [json.dumps(row)]) + "\n")
    print(f"\nrecorded in {HISTORY.name} ({sha[:9]}, load {row['loadavg']}) — commit it, that is the memory")


def selftest() -> int:
    assert unfit({"spread": 0.40, "loadavg": 1.0}), "runs disagreeing by 40% should be refused"
    assert unfit({"spread": 0.02, "loadavg": 9.0}), "three runs agreeing on a loaded machine only means they were slow together"
    assert not unfit({"spread": 0.02, "loadavg": 1.0}), "a quiet machine with runs that agree should be accepted"
    assert unfit({"spread": STEADY + 0.01, "loadavg": 0.1}) and not unfit({"spread": STEADY - 0.01, "loadavg": 0.1})
    assert unfit({"spread": 0.0, "loadavg": CALM + 0.1}) and not unfit({"spread": 0.0, "loadavg": CALM - 0.1})
    print("guard: refuses a jittery machine and a merely slow one, accepts a quiet one")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    update = "--update" in sys.argv

    if not BASELINE.exists() and not update:
        print(f"no baseline at {BASELINE} — run `python3 test/perf/guard.py --update` once, on a quiet machine")
        return 1

    now = measure()

    if update and (reason := unfit(now)):
        print(
            f"this machine is in no state to be baselined against: {reason}.\n"
            f"A baseline written now is a mood rather than a measurement — it is how the\n"
            f"old one came to sit 50% above what this machine does when it is quiet.\n\n"
            f"Try again when nothing else is running: it needs the {RUNS} runs within\n"
            f"{STEADY:.0%} of each other AND a load average under {CALM}."
        )
        return 1

    if update:
        BASELINE.write_text(json.dumps(now, indent=2) + "\n")
        print(f"baseline written to {BASELINE}:\n{json.dumps(now, indent=2)}")
        return 0

    was = json.loads(BASELINE.read_text())
    if was.get("scene") != now["scene"] or was.get("frames") != now["frames"]:
        print(f"baseline measured a different workload ({was.get('scene')}, {was.get('frames')} frames) — re-baseline before trusting it")
        return 1

    # Judging is refused on the same two grounds as baselining. A reading taken
    # on an unfit machine is not wrong, it is not comparable — and failing a
    # build on it teaches people to stop believing the gate.
    doubt = unfit(now)
    if doubt:
        print(f"reporting only, not judging: {doubt}.\n")

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

    if doubt:
        print("\nperformance: not judged — see above. Re-run when the machine is quiet.")
        return 0

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
