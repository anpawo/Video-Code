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
ancestor of the branch being published. That much only proves the commit
exists — every commit in the history does. The row that is about to be
published must also have *travelled* with its measurement: the commit carrying
the line is a child of the commit the line names, which is what `--record`
followed by a commit produces and what a number typed into a later pull request
cannot.

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


def introduced_by(sha: str) -> str:
    """The commit that added this row to the record, or "" if none did."""
    out = subprocess.run(
        ["git", "log", "--format=%H", "-S", sha, "--", str(HISTORY)],
        capture_output=True,
        text=True,
    )
    return out.stdout.split()[-1] if out.stdout.split() else ""


def measured(row: dict) -> str:
    """Empty if the row was really produced by a run; the reason otherwise.

    Ancestry alone proves nothing: every commit in the history is an ancestor,
    so a hand-typed row can name any of them and pass. What a fabricator cannot
    do is choose where the row *lands*. `guard.py --record` writes the number
    for the checkout it just measured, and that line then travels in the very
    next commit — so the commit holding the row is a child of the commit the
    row names. A row invented in a later pull request is added by a commit
    somewhere else entirely, and says so.
    """
    sha = str(row.get("sha", ""))
    adder = introduced_by(sha)
    if not adder:
        return f"{sha[:9]}: no commit ever added this line — it is not in the history it claims"
    parent = subprocess.run(["git", "rev-parse", f"{adder}^"], capture_output=True, text=True)
    if parent.returncode:
        return f"{sha[:9]}: added by the root commit {adder[:9]}, which measured nothing"
    if not parent.stdout.strip().startswith(sha):
        return (
            f"{sha[:9]}: added by {adder[:9]}, whose parent is {parent.stdout.strip()[:9]} — "
            "a measurement travels in the commit right after the one it measured, this one did not"
        )
    return ""


def append(path: Path) -> int:
    kept = [r for r in rows() if ancestor(str(r.get("sha", "")))]
    if not kept:
        print("perf history: nothing measured on this branch yet, publishing the bake counts alone")
        return 0

    last = kept[-1]
    # Only the row about to be published is held to this: it is the one that
    # reaches gh-pages, and every row faces the check on the push that
    # publishes it. Rows already on the curve are past the gate, for good or
    # ill.
    if reason := measured(last):
        print("the measurement about to be published was not measured here:")
        print(f"  {HISTORY.name}: {reason}")
        return 1

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


def selftest() -> int:
    known = {str(r.get("sha", "")) for r in rows()}
    victim = next(
        s
        for s in subprocess.run(["git", "rev-list", "-50", "HEAD"], capture_output=True, text=True).stdout.split()
        if s not in known
    )
    assert measured({"sha": victim}), f"{victim[:9]} never travelled with a measurement, and was accepted anyway"
    assert not measured(rows()[-1]), f"the recorded row was refused: {measured(rows()[-1])}"
    print("history: a row naming a commit it did not travel with is refused; the recorded one is not")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
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
