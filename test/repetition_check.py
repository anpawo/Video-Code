#!/usr/bin/env python3

"""
What the codebase says twice, and what it says to nobody.

Two questions a review never gets to in time, both answerable exactly:

  1. REPETITION — runs of lines that appear verbatim somewhere else, ignoring
     whitespace and comments. Measured on 2026-09-02: 343 lines across 68
     repetitions, and ten of them — up to 62 lines at a stretch — sit between
     `VulkanHeadlessRenderer.cpp` and `VulkanWidget.cpp`. The on-screen renderer
     and the headless one are near-copies, which is why a fix to one has to be
     remembered into the other by hand.

  2. DEAD SURFACE — public names defined in `videocode/` that nothing in the
     repository ever mentions: not the library, not the tests, not the C++, not
     the QML. Measured the same day: 22 of 391.

Neither is failed on outright, because both are pre-existing and this is a gate,
not a demolition order. What it refuses is GROWTH: the numbers are recorded in
`repetition.json` and the check fails when a commit makes either one worse. The
same shape as `test/perf/digest.py`, for the same reason — a number nobody can
see drifts, and a number that fails the day it is written gets disabled.

    python3 test/repetition_check.py            # compare against the record
    python3 test/repetition_check.py --update   # accept the current numbers
    python3 test/repetition_check.py --list     # say WHERE, for a human
"""

from __future__ import annotations

import ast
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

RECORD = Path(__file__).parent / "repetition.json"

# Long enough that a shared idiom — a Vulkan struct filled field by field, a
# guard clause — is not a finding, short enough to catch a copied function.
# At 6 the Vulkan boilerplate alone reported hundreds of hits; at 8 what is
# left is code someone actually duplicated.
WINDOW = 8

SOURCES = ("videocode/**/*.py", "src/**/*.cpp", "include/**/*.hpp")
# Scene files are meant to look alike — they are examples of the same idiom,
# and telling their authors to factor them would be telling them to stop
# writing examples.
SKIP = ("videocode/template/misc/example/",)


def sources() -> list[Path]:
    out: list[Path] = []
    for pattern in SOURCES:
        out += [p for p in Path().glob(pattern) if not any(s in str(p) for s in SKIP)]
    return sorted(out)


def meaningful(path: Path) -> list[tuple[int, str]]:
    """Lines that carry code, with their original numbers."""
    out = []
    for n, raw in enumerate(path.read_text(errors="replace").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(("#", "//", "*", "/*")):
            continue
        out.append((n, re.sub(r"\s+", " ", line)))
    return out


def repetitions() -> list[list[tuple[str, int, int, int]]]:
    """Maximal runs of code that appear more than once, grouped by content."""
    norm = {p: meaningful(p) for p in sources()}

    windows: dict[str, list[tuple[Path, int]]] = collections.defaultdict(list)
    for path, lines in norm.items():
        for i in range(len(lines) - WINDOW + 1):
            key = hashlib.sha256("\n".join(t for _, t in lines[i : i + WINDOW]).encode()).hexdigest()
            windows[key].append((path, i))

    # A window seen twice is hot; consecutive hot windows are one repetition,
    # not eight — without this, a copied 60-line function reports 53 times.
    hot: dict[Path, set[int]] = collections.defaultdict(set)
    for spots in windows.values():
        if len(spots) > 1:
            for path, i in spots:
                hot[path].add(i)

    runs = []
    for path, idxs in hot.items():
        for i in sorted(idxs):
            if i - 1 in idxs:
                continue
            j = i
            while j + 1 in idxs:
                j += 1
            runs.append((path, i, j + WINDOW - 1))

    byContent: dict[str, list[tuple[str, int, int, int]]] = collections.defaultdict(list)
    for path, i, j in runs:
        lines = norm[path]
        body = "\n".join(t for _, t in lines[i : j + 1])
        byContent[hashlib.sha256(body.encode()).hexdigest()].append((str(path), lines[i][0], lines[j][0], j - i + 1))

    return sorted((g for g in byContent.values() if len(g) > 1), key=lambda g: -g[0][3])


def deadSurface() -> list[tuple[str, int, str]]:
    """Public names in videocode/ that nothing anywhere mentions."""
    defined: dict[str, tuple[str, int]] = {}
    for p in Path().glob("videocode/**/*.py"):
        try:
            tree = ast.parse(p.read_text())
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_") and node.name != "main":
                    defined.setdefault(node.name, (str(p), node.lineno))

    used: collections.Counter[str] = collections.Counter()
    for pattern in ("videocode/**/*.py", "test/**/*.py", "docs/**/*.py", "*.py"):
        for p in Path().glob(pattern):
            try:
                tree = ast.parse(p.read_text())
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used[node.id] += 1
                elif isinstance(node, ast.Attribute):
                    used[node.attr] += 1
                elif isinstance(node, ast.keyword) and node.arg:
                    used[node.arg] += 1

    # C++ and QML reach into Python BY NAME — pybind calls and QML bindings are
    # invisible to the AST walk, and a name only they use is not dead.
    reachable = "\n".join(
        p.read_text(errors="replace") for pattern in ("src/**/*.cpp", "src/**/*.hpp", "qml/**/*.qml") for p in Path().glob(pattern)
    )

    dead = []
    for name, (file, line) in sorted(defined.items()):
        if used[name] == 0 and not re.search(rf"\b{re.escape(name)}\b", reachable):
            dead.append((file, line, name))
    return dead


def measure() -> dict:
    groups = repetitions()
    return {
        "repeatedLines": sum(g[0][3] for g in groups),
        "repetitions": len(groups),
        "deadNames": len(deadSurface()),
    }


def main() -> int:
    now = measure()

    if "--list" in sys.argv:
        for group in repetitions()[:20]:
            print(f"  {group[0][3]} lines, {len(group)} copies:")
            for file, first, last, _ in group:
                print(f"      {file}:{first}-{last}")
        print()
        for file, line, name in deadSurface():
            print(f"  {file}:{line}  {name}  — nothing mentions this")
        return 0

    if "--update" in sys.argv or not RECORD.exists():
        RECORD.write_text(json.dumps(now, indent=2) + "\n")
        print(f"recorded: {now}")
        return 0

    was = json.loads(RECORD.read_text())
    worse = [k for k in now if now[k] > was.get(k, 0)]
    for key, label in (
        ("repeatedLines", "lines said twice"),
        ("repetitions", "distinct repetitions"),
        ("deadNames", "public names nothing uses"),
    ):
        arrow = "←" if key in worse else " "
        print(f"  {label:<28} {was.get(key, 0):>6} → {now[key]:>6}  {arrow}")

    if worse:
        print("\nThis commit adds repetition or surface nobody reaches.")
        print("`python3 test/repetition_check.py --list` says where.")
        print("Deliberate? `--update` records the new numbers, and the diff shows you decided.")
        return 1

    if any(now[k] < was.get(k, 0) for k in now):
        print("\nless than there was — run `--update` to keep the win")
    return 0


if __name__ == "__main__":
    sys.exit(main())
