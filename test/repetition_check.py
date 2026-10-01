#!/usr/bin/env python3

"""
What the codebase says twice, and what it says to nobody.

Two questions a review never gets to in time, both answerable exactly:

  1. REPETITION — runs of lines that appear verbatim somewhere else, ignoring
     whitespace and comments, in the Python, the C++, the QML and the GLSL.
     Measured on 2026-09-18: 1691 lines across 119 repetitions, and 46 of them
     — 834 lines, up to 62 at a stretch — sit between
     `VulkanHeadlessRenderer.cpp` and `VulkanWidget.cpp`. The on-screen renderer
     and the headless one are near-copies, which is why a fix to one has to be
     remembered into the other by hand.

  2. DEAD SURFACE — public names defined in `videocode/` that nothing in the
     repository ever mentions: not the library, not the tests, not the C++, not
     the QML. Measured the same day: 19.

Neither is failed on outright, because both are pre-existing and this is a gate,
not a demolition order. What it refuses is what is NEW: `repetition.json` records
every clone by the hash of its content — no line numbers in it, so editing above
a clone changes nothing — and the check fails on a clone the record does not
know, even when the totals fall. Three integers could not see one clone deleted
and another written. Dead names keep the simpler rule: the count may not grow.
The same shape as `test/perf/digest.py`, for the same reason — a number nobody
can see drifts, and a number that fails the day it is written gets disabled.

`twins.json` lists the pairs that are alike ON PURPOSE, each with its reason.
Inside a pair the rule is growth, not identity — a bug fixed on both sides
changes the hashes and must stay green — and a clone that VANISHES from a pair
is printed, because that is what a fix applied to one side only looks like.

    python3 test/repetition_check.py            # compare against the record
    python3 test/repetition_check.py --update   # accept what is there now
    python3 test/repetition_check.py --list     # say WHERE, for a human
    python3 test/repetition_check.py --candidates out.json [--since <ref>]
                                                # what the weekly audit reads

`--candidates` is for the weekly audit routine: the clones outside the
declared twins, and an index of every function with the ones touched since
`<ref>` (default: the last 8 days) marked. The index is the point — two
functions doing one job with different code never show up as a verbatim clone,
so a list of clones alone would hand the agent only what `--list` prints for
free.
"""

from __future__ import annotations

import ast
import collections
import hashlib
import json
import re
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

RECORD = Path(__file__).parent / "repetition.json"
TWINS = Path(__file__).parent / "twins.json"

# Long enough that a shared idiom — a Vulkan struct filled field by field, a
# guard clause — is not a finding, short enough to catch a copied function.
# At 6 the Vulkan boilerplate alone reported hundreds of hits; at 8 what is
# left is code someone actually duplicated.
WINDOW = 8

SOURCES = (
    "videocode/**/*.py",
    "src/**/*.cpp",
    "include/**/*.hpp",
    "qml/**/*.qml",
    "assets/shaders/**/*.glsl",
    "assets/mathshaders/**/*.glsl",
)
# Scene files are meant to look alike — they are examples of the same idiom,
# and telling their authors to factor them would be telling them to stop
# writing examples.
SKIP = ("videocode/template/misc/example/",)


def sources() -> list[Path]:
    out: list[Path] = []
    for pattern in SOURCES:
        out += [p for p in Path().glob(pattern) if not any(s in str(p) for s in SKIP)]
    return sorted(out)


# What opens a line that carries no code. `#` stays on the C family too: an
# include block or a `#version` two files share is not something anyone copied.
# Python loses `*` — there it opens `*args,` in a wrapped signature, not a
# comment.
NOT_CODE = {".py": ("#",)}
NOT_CODE_C = ("#", "//", "*", "/*")

# file, first line, last line, lines of code
Spot = tuple[str, int, int, int]


def meaningful(path: Path) -> list[tuple[int, str]]:
    """Lines that carry code, with their original numbers."""
    out = []
    for n, raw in enumerate(path.read_text(errors="replace").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(NOT_CODE.get(path.suffix, NOT_CODE_C)):
            continue
        out.append((n, re.sub(r"\s+", " ", line)))
    return out


def clones(norm: dict[str, list[tuple[int, str]]]) -> dict[str, list[Spot]]:
    """Maximal runs of code that appear more than once, keyed by content."""
    keys = {
        file: [hashlib.sha256("\n".join(t for _, t in lines[i : i + WINDOW]).encode()).hexdigest() for i in range(len(lines) - WINDOW + 1)]
        for file, lines in norm.items()
    }
    windows: dict[str, list[tuple[str, int]]] = collections.defaultdict(list)
    for file, ks in keys.items():
        for i, key in enumerate(ks):
            windows[key].append((file, i))

    # Matched PAIR by pair, and grown while both sides still agree — without
    # the growing, a copied 60-line function reports 53 times. It used to be
    # grown file by file instead: every window seen twice was merged with its
    # neighbours, so a function copied from B sitting right after one copied
    # from C became one run whose content matched neither B nor C, and all
    # three were dropped. 16 runs of 155, 359 lines, on 2026-09-18.
    found: dict[str, set[Spot]] = collections.defaultdict(set)
    for spots in windows.values():
        for n, (fa, i) in enumerate(spots):
            for fb, j in spots[n + 1 :]:
                ka, kb = keys[fa], keys[fb]
                # A run that overlaps its own copy is a table of identical
                # lines, not something said twice.
                if fa == fb and j - i < WINDOW:
                    continue
                if i and j and ka[i - 1] == kb[j - 1]:
                    continue  # the pair one line up grows into this one
                more = 0
                while i + more + 1 < len(ka) and j + more + 1 < len(kb) and ka[i + more + 1] == kb[j + more + 1] and (fa != fb or i + more + 1 + WINDOW <= j):
                    more += 1
                size = more + WINDOW
                body = "\n".join(t for _, t in norm[fa][i : i + size])
                # Eight closing braces in a row are in every deeply nested QML
                # file, and nobody copied them.
                if not any(c.isalnum() for c in body):
                    continue
                for file, at in ((fa, i), (fb, j)):
                    lines = norm[file]
                    found[hashlib.sha256(body.encode()).hexdigest()[:16]].add((file, lines[at][0], lines[at + size - 1][0], size))

    return {h: sorted(found[h]) for h in sorted(found, key=lambda h: (-next(iter(found[h]))[3], h))}


def repetitions() -> dict[str, list[Spot]]:
    return clones({str(p): meaningful(p) for p in sources()})


def declared(files: set[str]) -> str:
    """The declared twin these files all belong to, or "" — see twins.json."""
    if len(files) > 1:
        for twin in json.loads(TWINS.read_text()):
            if all(any(fnmatch(f, pattern) for pattern in twin["files"]) for f in files):
                return " ↔ ".join(twin["files"])
    return ""


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
    record: dict = {"clones": {}, "twins": {}}
    groups = repetitions()
    for identity, spots in groups.items():
        twin = declared({s[0] for s in spots})
        first = next(t for n, t in meaningful(Path(spots[0][0])) if n >= spots[0][1] and any(c.isalpha() for c in t))
        where = record["twins"].setdefault(twin, {}) if twin else record["clones"]
        where[identity] = [spots[0][3], len(spots), first]
    return {
        "repeatedLines": sum(g[0][3] for g in groups.values()),
        "repetitions": len(groups),
        "deadNames": len(deadSurface()),
        **record,
    }


def write(record: dict) -> None:
    # One clone per line, opened by its first line of code: the diff of this
    # file is where a new clone gets accepted, and a bare hash says nothing to
    # the person accepting it.
    text = json.dumps(record, indent=2, ensure_ascii=False)
    RECORD.write_text(re.sub(r"\[\s+(\d+),\s+(\d+),\s+(\".*\")\s+\]", r"[\1, \2, \3]", text) + "\n")


def where(spots: list[Spot]) -> str:
    return " ↔ ".join(f"{file}:{first}" for file, first, _, _ in spots) + f" ({spots[0][3]} lines)"


def verdict(was: dict, now: dict) -> tuple[list[str], list[tuple[str, int, int, list[str]]], list[tuple[str, int, str]]]:
    """The clones the record does not know, the twins that grew, and what a twin lost."""
    # IDENTITIES, not totals: a total stays level when one clone is deleted and
    # another is written, which is a new clone all the same. One more copy of
    # a known clone counts too.
    known = was.get("clones", {})
    new = [h for h, (_, copies, _) in now["clones"].items() if h not in known or copies > known[h][1]]

    # Inside a declared twin the rule is growth: a bug fixed on BOTH sides
    # changes the hashes and must not go red for it.
    grown, gone = [], []
    for twin in sorted(now["twins"].keys() | was.get("twins", {}).keys()):
        before, after = was.get("twins", {}).get(twin, {}), now["twins"].get(twin, {})
        fresh = [h for h in after if h not in before]
        lines = [sum(v[0] for v in side.values()) for side in (before, after)]
        if lines[1] > lines[0]:
            grown.append((twin, lines[0], lines[1], fresh))
        # A clone that leaves the pair with nothing its size taking its place
        # is what a fix applied to one side only looks like.
        for h, (size, _, first) in before.items():
            if h not in after and size not in [after[f][0] for f in fresh]:
                gone.append((twin, size, first))
    return new, grown, gone


def changedLines(since: str) -> dict[str, list[tuple[int, int]]]:
    """Per file, the line ranges that differ from `since`. Empty when git cannot say."""
    if not since:
        week = subprocess.run(["git", "log", "--since=8 days ago", "--format=%H"], capture_output=True, text=True).stdout.split()
        since = f"{week[-1]}^" if week else "HEAD"
    diff = subprocess.run(["git", "diff", "-U0", since, "--", "videocode", "src", "include"], capture_output=True, text=True)
    if diff.returncode:
        print(f"git cannot diff against {since} — nothing is marked changed", file=sys.stderr)
    out: dict[str, list[tuple[int, int]]] = collections.defaultdict(list)
    file = ""
    for line in diff.stdout.splitlines():
        if line.startswith("+++ "):
            file = line[6:]
        elif hunk := re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))?", line):
            start, count = int(hunk[1]), int(hunk[2] or 1)
            out[file].append((start, start + max(count, 1) - 1))
    return out


# A definition the way clang-format leaves it here: the name and its opening
# parenthesis on one line, then `{` before any `;`. Pragmatic, and it says what
# it misses: lambdas, operators, macros that define functions, and anything
# whose return type sits alone on the line above.
CPP_DEF = re.compile(r"^\s*(?![:,])(?:[\w:<>,*&~\[\]]+\s+)*?[*&]*((?:\w+::)*~?\w+)\s*\(")
NOT_A_NAME = {"if", "for", "while", "switch", "return", "catch", "sizeof", "static_assert", "else", "do", "new", "delete"}


def functions(since: str) -> dict[str, list[dict]]:
    """Every function, by file — where two that do one job with different code can be found."""
    changed = changedLines(since)

    def entry(file: str, first: int, last: int, **fields) -> dict:
        touched = any(a <= last and first <= b for a, b in changed.get(file, ()))
        return {**fields, "line": first, **({"changed": True} if touched else {})}

    out: dict[str, list[dict]] = {}
    for p in sorted(Path().glob("videocode/**/*.py")):
        if any(s in str(p) for s in SKIP):
            continue
        try:
            tree = ast.parse(p.read_text())
        except (OSError, SyntaxError):
            continue

        def walk(node: ast.AST, prefix: str) -> None:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    last = child.end_lineno or child.lineno
                    returns = f" -> {ast.unparse(child.returns)}" if child.returns else ""
                    doc = (ast.get_docstring(child) or "").strip().splitlines()
                    out.setdefault(str(p), []).append(
                        entry(
                            str(p),
                            child.lineno,
                            last,
                            name=prefix + child.name,
                            sig=f"({ast.unparse(child.args)}){returns}",
                            **({"doc": doc[0][:100]} if doc else {}),
                            lines=last - child.lineno + 1,
                        )
                    )
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    walk(child, f"{prefix}{child.name}.")

        walk(tree, "")

    for pattern in ("src/**/*.cpp", "include/**/*.hpp"):
        for p in sorted(Path().glob(pattern)):
            text = p.read_text(errors="replace").splitlines()
            found = []
            for n, line in enumerate(text):
                m = CPP_DEF.match(line)
                # `](` or `] {` is a call taking a lambda — `connect(a, &A::b, this, [this]() {`.
                if not m or m[1] in NOT_A_NAME or line.rstrip().endswith(";") or re.search(r"\]\s*[({]", line):
                    continue
                rest = next((t.strip() for t in text[n + 1 :] if t.strip().startswith("{") or t.rstrip().endswith(";")), "")
                if line.rstrip().endswith("{") or rest.startswith("{"):
                    found.append((m[1], n + 1))
            # No parser, so no end of body: a function runs to the next one.
            for (name, first), (_, nxt) in zip(found, found[1:] + [("", len(text) + 2)]):
                out.setdefault(str(p), []).append(entry(str(p), first, nxt - 1, name=name))
    return out


def candidates(path: Path, since: str) -> None:
    clonesOut = [
        {"id": identity, "lines": spots[0][3], "at": [f"{file}:{first}-{last}" for file, first, last, _ in spots]}
        for identity, spots in repetitions().items()
        if not declared({s[0] for s in spots})
    ]
    index = functions(since)
    path.write_text(json.dumps({"clones": clonesOut, "functions": index}, separators=(",", ":"), ensure_ascii=False) + "\n")
    every = [f for fs in index.values() for f in fs]
    print(f"{path}: {len(clonesOut)} clones, {len(every)} functions, {sum('changed' in f for f in every)} changed — {path.stat().st_size // 1024} KB")


def main() -> int:
    if "--candidates" in sys.argv:
        since = sys.argv[sys.argv.index("--since") + 1] if "--since" in sys.argv else ""
        candidates(Path(sys.argv[sys.argv.index("--candidates") + 1]), since)
        return 0

    groups = repetitions()

    if "--list" in sys.argv:
        for spots in list(groups.values())[:20]:
            twin = "  — declared twin" if declared({s[0] for s in spots}) else ""
            print(f"  {spots[0][3]} lines, {len(spots)} copies:{twin}")
            for file, first, last, _ in spots:
                print(f"      {file}:{first}-{last}")
        print()
        for file, line, name in deadSurface():
            print(f"  {file}:{line}  {name}  — nothing mentions this")
        return 0

    now = measure()

    if "--update" in sys.argv or not RECORD.exists():
        write(now)
        print("recorded: " + ", ".join(f"{k} {now[k]}" for k in ("repeatedLines", "repetitions", "deadNames")))
        return 0

    was = json.loads(RECORD.read_text())
    for key, label in (
        ("repeatedLines", "lines said twice"),
        ("repetitions", "distinct repetitions"),
        ("deadNames", "public names nothing uses"),
    ):
        arrow = "←" if key == "deadNames" and now[key] > was.get(key, 0) else " "
        print(f"  {label:<28} {was.get(key, 0):>6} → {now[key]:>6}  {arrow}")

    new, grown, gone = verdict(was, now)
    for twin, size, first in gone:
        print(f"\n  warning: {twin} no longer share {size} lines starting `{first}`")
        print("           — was this fixed on one side only?")

    if new:
        print("\nSaid twice, and not in the record:")
        print("\n".join(f"  {where(groups[h])}" for h in new))
    for twin, before, after, fresh in grown:
        print(f"\nA declared twin may change, it may not grow — {before} → {after} repeated lines:")
        print(f"  {twin}")
        print("\n".join(f"    {where(groups[h])}" for h in fresh))
    dead = now["deadNames"] > was.get("deadNames", 0)
    if dead:
        print("\nThis commit adds surface nobody reaches.")
        print("`python3 test/repetition_check.py --list` says where.")
    if new or grown or dead:
        print("\nDeliberate? `--update` records it, and the diff shows you decided.")
        return 1

    if now != was:
        print("\nnot what the record says, and no worse — run `--update` to keep it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
