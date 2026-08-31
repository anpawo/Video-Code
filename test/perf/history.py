#!/usr/bin/env python3

"""
The perf numbers, kept.

`guard.py --record` appends one line per measurement to `history.jsonl`, which
travels in the commit like a golden. This reads that file: `--verify` says
whether it can be trusted, `--append` hands its last row to the CI job that
publishes the curve.

    python3 test/perf/history.py --verify              # is the record sound?
    python3 test/perf/history.py --append bench.json   # add it to what CI plots

Why verify at all
─────────────────
`history.jsonl` is a tracked file, so any pull request can write it, and a row
typed by hand is indistinguishable by eye from a measured one. One wrong row
poisons the curve for good — and the curve IS the memory this exists to build.
So every row must name the commit it measured, and that commit must be a real
ancestor of the branch being published. A number nobody measured has no commit
it can point at.

Only numbers cross into the published file: the labels are literals written
here, never text read from the record.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HISTORY = Path(__file__).parent / "history.jsonl"

# field -> (low, high). Wide enough to hold a machine ten times slower or ten
# times faster than this one; narrow enough that a typo or a placeholder is not
# a plausible measurement.
RANGE = {
    "load": (0.05, 600.0),
    "msPerFrame": (0.05, 10_000.0),
    "total": (0.05, 3_600.0),
    "rssMb": (16.0, 65_536.0),
    "frames": (1, 100_000),
}


def rows() -> list[dict]:
    if not HISTORY.exists():
        return []
    out = []
    for n, line in enumerate(HISTORY.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise SystemExit(f"{HISTORY.name}:{n}: not JSON ({e})")
    return out


def ancestor(sha: str) -> bool:
    if subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], capture_output=True).returncode:
        return False
    return subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"], capture_output=True).returncode == 0


def verify() -> int:
    seen: dict[str, int] = {}
    bad: list[str] = []
    for n, row in enumerate(rows(), 1):
        sha = row.get("sha", "")
        if not isinstance(sha, str) or len(sha) < 7 or not all(c in "0123456789abcdef" for c in sha):
            bad.append(f"{HISTORY.name}:{n}: `sha` is not a commit hash")
            continue
        if sha in seen:
            bad.append(f"{HISTORY.name}:{n}: {sha[:9]} already measured on line {seen[sha]}")
        seen[sha] = n
        if not ancestor(sha):
            bad.append(f"{HISTORY.name}:{n}: {sha[:9]} is not an ancestor of HEAD — nobody measured this commit here")
        for field, (low, high) in RANGE.items():
            value = row.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not low <= value <= high:
                bad.append(f"{HISTORY.name}:{n}: `{field}` = {value!r}, expected a number in [{low}, {high}]")

    if bad:
        print("the perf record does not hold up:")
        print("\n".join(f"  {b}" for b in bad))
        return 1
    print(f"perf history: {len(seen)} measurement(s), every one on a commit that exists here")
    return 0


def append(path: Path) -> int:
    kept = [r for r in rows() if ancestor(str(r.get("sha", "")))]
    if not kept:
        print("perf history: nothing measured on this branch yet, publishing the bake counts alone")
        return 0

    last = kept[-1]
    published = json.loads(path.read_text()) if path.exists() else []
    published += [
        {"name": "render/msPerFrame", "unit": "ms", "value": float(last["msPerFrame"])},
        {"name": "render/total", "unit": "s", "value": float(last["total"])},
        {"name": "render/load", "unit": "s", "value": float(last["load"])},
        {"name": "render/peakRss", "unit": "MB", "value": float(last["rssMb"])},
    ]
    path.write_text(json.dumps(published, indent=1) + "\n")
    print(f"perf history: published the measurement of {str(last['sha'])[:9]}")
    return 0


def main() -> int:
    if "--verify" in sys.argv:
        return verify()
    if "--append" in sys.argv:
        if verify():
            return 1
        return append(Path(sys.argv[sys.argv.index("--append") + 1]))
    print(__doc__.strip().splitlines()[0])
    return 1


if __name__ == "__main__":
    sys.exit(main())
