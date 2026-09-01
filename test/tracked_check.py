#!/usr/bin/env python3

"""
Does the repository contain what its own tooling calls?

Every gate here reads what a change ADDS. None of them reads what a commit
FORGETS — so a commit that deletes two workflows and leaves their replacements
untracked passes coverage, pyright and the QML check, and lands a repository
with no CI at all. That is the same defect as a green that does not depend on
what it checks, turned inside out.

It has four other faces, all measured: a dependency commented out of
requirements.txt (eight weeks of red CI), assets gitignored (two scenes that
cannot bake from a clean clone), an uncommitted cache of an unpinned apt binary,
and a bake-time network fetch. One sentence covers them: the repository does not
contain what it needs to run anywhere else.

This walks the files that DRIVE the build — the Makefile, the workflows, the
hook — and checks that every repository path they name is actually in git.

    python3 test/tracked_check.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

DRIVERS = ["Makefile", "CMakeLists.txt", ".githooks/pre-commit", *sorted(str(p) for p in Path(".github/workflows").glob("*.yaml"))]

# A path is only checked when it names a directory this repository owns and ends
# in a real extension: `$(nproc)`, `refs/heads/main` and `v1.22.1` are not files.
PATH = re.compile(r"\b((?:test|src|include|videocode|assets|qml|docs|scripts|vcpkg-overlay-ports)/[\w./-]+\.(?:py|cpp|hpp|mm|sh|json|jsonl|yaml|yml|qml|glsl|txt|md|cmake))")


# A driver can depend on a whole directory without ever naming a file in one:
# `QML_DIR="${CMAKE_SOURCE_DIR}/qml"` and `qmllint -I qml $(find qml ...)` both
# do. That shape has no extension to match, and it is exactly the shape that
# kept all 21 files of `qml/` out of the repository while `--check-chrome` was
# being promoted to a hook gate.
def owned() -> list[str]:
    """Top-level directories this repository is supposed to hold — build output
    and caches excluded by asking git, not by keeping a list that would rot."""
    here = [d.name for d in Path(".").iterdir() if d.is_dir() and not d.name.startswith(".")]
    ignored = subprocess.run(["git", "check-ignore", *here], capture_output=True, text=True).stdout.split()
    return sorted(set(here) - set(ignored))


def tracked() -> set[str]:
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=A"], capture_output=True, text=True).stdout
    return set(out.split()) | set(staged.split())


def code(text: str) -> str:
    """The driver without its comments — a path named in prose is not a call."""
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def main() -> int:
    known = tracked()
    ours = owned()
    missing: list[str] = []
    for driver in DRIVERS:
        text = code(Path(driver).read_text()) if Path(driver).exists() else ""
        for path in sorted(set(PATH.findall(text))):
            if path in known or not Path(path).exists():
                # A path that exists nowhere is a different bug — a typo or a
                # file the driver creates — and this check would only guess.
                continue
            missing.append(f"  {driver} calls {path}, which is not in the repository")

        # A directory is named bare — `-I qml`, `${CMAKE_SOURCE_DIR}/qml` — so
        # there is no extension to look for. Ask the other way round: of the
        # directories this repository owns, which does the driver mention?
        for name in ours:
            if not re.search(rf"(?<![\w.-]){re.escape(name)}(?![\w-])", text):
                continue
            if not subprocess.run(["git", "ls-files", name], capture_output=True, text=True).stdout.strip():
                missing.append(f"  {driver} names {name}/, and the repository knows no file inside it")

    # A scene on disk that no case names is a scene no golden ever renders.
    #
    # `digest.py` finds scenes by glob, so a new one is picked up automatically
    # and, once `--update` has run, accepted forever — its stack shape is
    # checked and its PIXELS are not. `kGoldenCases` is a hand-kept C++ list;
    # the two agreed at 49/49 when this was written, and nothing made them.
    scenes = {p.name for p in Path("test/visual/scenes").glob("*.py")}
    cases = {Path(m).name for m in re.findall(r"test/visual/scenes/[\w.]+\.py", code(Path("src/test/VisualTest.cpp").read_text()))}
    for orphan in sorted(scenes - cases):
        missing.append(f"  test/visual/scenes/{orphan} is rendered by no case in VisualTest.cpp — the digest sees it, no golden does")
    for ghost in sorted(cases - scenes):
        missing.append(f"  VisualTest.cpp names test/visual/scenes/{ghost}, which is not on disk")

    if missing:
        print("what this repository names and what it holds have come apart:")
        print("\n".join(missing))
        print("\nCommit what is missing, or register what is unregistered — a driver")
        print("that calls a file nobody has is red for everyone but you, and a scene")
        print("no case names is a scene no golden ever renders.")
        return 1

    print(f"every path the build drivers name is in the repository ({len(DRIVERS)} drivers)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
