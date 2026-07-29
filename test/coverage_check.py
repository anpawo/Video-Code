#!/usr/bin/env python3

"""
Are the things this commit ADDS documented and tested?

Deterministic gate for the pre-commit hook: it never writes anything, it only
reports what a human (or `/ship`) still owes. Judgement calls — is this
docstring any good, does the example actually teach — are not its business.

What counts as owed, for every public symbol the diff adds to the LIBRARY:

  1. a docstring / doc comment where it is defined (.py, .cpp, .hpp)
  2. a mention in docs/*.md — the file a new user actually opens
  3. a mention in test/ — something that would fail if the symbol broke

Private names (leading underscore) are exempt: they are not surface. Scene
files at the repo root (video.py, eg.py, feat.py) are exempt too — they are
usage, not API.

Python additions are confirmed by PARSING the file, not by trusting the diff:
a `def` inside a docstring example is not a definition, and one such example
in `ishader.py` fooled the first version of this script.

    python3 test/coverage_check.py            # staged changes (pre-commit)
    python3 test/coverage_check.py --pushed   # everything not yet on the remote
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

# Only the library owes documentation. Scenes and tests are readers, not surface.
LIBRARY = ("videocode/", "src/", "include/")
CPP_DEF = re.compile(r"^\+\s*(?:class|struct)\s+([A-Za-z]\w*)")
PY_DEF = re.compile(r"^\+\s*(?:def|class)\s+([A-Za-z]\w*)")


def run(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True).stdout


def diff(pushed: bool) -> str:
    if not pushed:
        return run("git", "diff", "--cached", "-U0")
    upstream = run("git", "rev-parse", "--abbrev-ref", "@{upstream}").strip()
    return run("git", "diff", f"{upstream or 'HEAD~1'}...HEAD", "-U0")


def pyDefinitions(path: str) -> dict[str, ast.AST]:
    """Real top-level and class-level definitions, by name — docstring examples excluded."""
    try:
        tree = ast.parse(Path(path).read_text())
    except (OSError, SyntaxError):
        return {}
    out: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = node
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out.setdefault(child.name, child)
    return out


def addedSymbols(patch: str) -> dict[str, str]:
    """{symbol: file} for public additions to the library, confirmed against the file."""
    found: dict[str, str] = {}
    current = ""
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            continue
        if not any(current.startswith(d) for d in LIBRARY):
            continue

        if current.endswith(".py"):
            m = PY_DEF.match(line)
            if m and not m.group(1).startswith("_") and m.group(1) in pyDefinitions(current):
                found.setdefault(m.group(1), current)
        elif current.endswith((".cpp", ".hpp")):
            m = CPP_DEF.match(line)
            if m and not m.group(1).startswith("_"):
                found.setdefault(m.group(1), current)
    return found


def mentioned(symbol: str, where: str) -> bool:
    return bool(run("grep", "-rl", symbol, where).strip())


def documented(symbol: str, path: str) -> bool:
    if path.endswith(".py"):
        node = pyDefinitions(path).get(symbol)
        return node is None or bool(ast.get_docstring(node))  # type: ignore[arg-type]

    try:
        lines = Path(path).read_text().splitlines()
    except OSError:
        return True
    for i, line in enumerate(lines):
        if re.match(rf"^\s*(?:class|struct)\s+{re.escape(symbol)}\b", line):
            before = "\n".join(lines[max(0, i - 5) : i])
            return "//" in before or "/*" in before
    return True


def main() -> int:
    symbols = addedSymbols(diff("--pushed" in sys.argv))
    if not symbols:
        print("coverage: nothing public added to the library")
        return 0

    owed: list[str] = []
    for symbol, path in sorted(symbols.items()):
        missing = []
        if not documented(symbol, path):
            missing.append("a docstring where it is defined")
        if not mentioned(symbol, "docs"):
            missing.append("a mention in docs/*.md")
        if not mentioned(symbol, "test"):
            missing.append("a test that would fail if it broke")
        if missing:
            owed.append(f"  {symbol}  ({path})\n" + "".join(f"      needs {m}\n" for m in missing))

    if not owed:
        print(f"coverage: {len(symbols)} public addition(s), all documented and tested")
        return 0

    print(f"coverage: {len(owed)} of {len(symbols)} public addition(s) still owe something\n")
    print("".join(owed))
    print("Run  /ship  to write what is missing — including a runnable example — then commit again.")
    print("Deliberate exception? Commit with  --no-verify  and say why in the message.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
