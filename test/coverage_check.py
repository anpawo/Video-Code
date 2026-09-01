#!/usr/bin/env python3

"""
Are the things this commit ADDS documented and tested?

Deterministic gate for the pre-commit hook: it never writes anything, it only
reports what a human (or `/ship`) still owes. Judgement calls — is this
docstring any good, does the example actually teach — are not its business.

What counts as owed, for every public symbol the diff adds to the LIBRARY:

  1. a docstring / doc comment where it is defined (.py, .cpp, .hpp)
  2. a mention in docs/*.md — the file a new user actually opens
  3. a USE in test/ — for Python, the name has to appear as an identifier in a
     file that parses, not as text a grep found in a comment

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
from functools import cache
from pathlib import Path

# Only the library owes documentation. Scenes and tests are readers, not surface.
LIBRARY = ("videocode/", "src/", "include/")
# A forward declaration is not surface: `class ArgumentParser;` promises a name,
# not an API, and asking it for documentation sends the author hunting for a type
# this repository does not own. The rest of the line decides — requiring a body
# on the SAME line looked equivalent and was not: this project opens its braces
# on the next line, so that version stopped seeing `struct Rule` entirely. A gate
# that under-reports is worse than one that over-reports.
CPP_DEF = re.compile(r"^\+\s*(?:class|struct)\s+([A-Za-z]\w*)(?P<rest>.*)$")
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
        # Headers only: a type declared in a .cpp is reachable by nobody, so it
        # is not surface. A helper struct local to one function was asking for
        # a documentation page — a false alarm, and a false alarm on a hook is
        # how a team learns to type --no-verify.
        elif current.endswith(".hpp"):
            m = CPP_DEF.match(line)
            if m and m.group("rest").split("//")[0].strip().startswith(";"):
                continue
            if m and not m.group(1).startswith("_"):
                found.setdefault(m.group(1), current)
    return found


@cache
def testIdentifiers() -> frozenset[str]:
    """Every name the Python tests actually USE — prose and comments excluded."""
    names: set[str] = set()
    for path in Path("test").rglob("*.py"):
        try:
            tree = ast.parse(path.read_text())
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
    return frozenset(names)


def mentioned(symbol: str, where: str) -> bool:
    # -w, not a bare match: without it `Scen` is "mentioned" by every page that
    # says Scene, and a symbol named after a common word is documented by
    # accident. Three docs pages pass the substring and none of them the word.
    return bool(run("grep", "-rlw", symbol, where).strip())


def tested(symbol: str, path: str) -> bool:
    """Is the symbol exercised by a test, rather than merely named in one?

    For Python the tests are Python, so this is answerable: the symbol has to
    appear as an identifier in a file that parses. A grep also said yes to the
    symbol sitting in a comment, in a docstring, or in a `# TODO: test this`
    — which is precisely the thing the report is supposed to catch.

    C++ surface is exercised from test/cpp, and parsing C++ to find out costs
    more than this gate is worth. The word-boundary grep is the honest bar
    there, and it is weaker: it cannot tell a use from a mention.
    """
    if path.endswith(".py"):
        return symbol in testIdentifiers()
    return mentioned(symbol, "test")


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


def selftest() -> int:
    assert not mentioned("Scen", "docs"), "a substring of Scene should not count as a mention of Scen"
    assert mentioned("Scene", "docs"), "Scene is named in docs and should count"
    assert "coverage_check" not in testIdentifiers(), "a module name in prose is not a use"
    assert "print" in testIdentifiers(), "print is used all over test/ and should be seen"
    print("coverage_check: word boundaries hold, and a use is told apart from a mention")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
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
        if not tested(symbol, path):
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
