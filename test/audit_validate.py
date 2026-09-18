#!/usr/bin/env python3

"""
What the weekly audit agent said, held against the repository before anyone
reads it.

The agent in `.github/workflows/audit.yaml` writes JSON. Nothing it writes is
trusted: a line range is checked against the file, a declared twin is dropped,
advice the owner has already refused is dropped, a claim about speed is dropped
— the agent asks, the Mac measures. What survives gets an ID made from the code
it cites, so the same finding is never posted twice, and at most three leave.

There is deliberately NO text-similarity floor between the two spans: the one
thing only an agent can find is two functions doing one job with different
code, and a similarity floor rejects exactly that.

    python3 test/audit_validate.py run.json                 # print what survives
    python3 test/audit_validate.py run.json -o findings.json

`run.json` is either the agent's JSON itself or the envelope `claude -p
--output-format json` wraps it in. Exit 1 only when there is no JSON to read;
a rejected finding is a line on stderr, not a failure.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from repetition_check import declared, meaningful

MOST = 3
KINDS = ("duplicate", "dead", "perf-question")
LIMITS = {"title": 80, "why": 600, "delete": 400}

# A tripwire, not a judge: it knows nothing about design, it only catches the
# agent saying the words the owner has answered already — deletion over
# addition. An abstraction proposed in other words gets through, and is closed
# by hand, which is what closing an `audit` issue is for.
REFUSED = ("base class", "superclass", "abstraction", "mixin", "helper module", "new helper", "shared helper", "new module", "new class")

# The performance seat's rule. A runner has no GPU and the agent has no clock:
# whatever number it writes, it made up.
SPEED_CLAIM = re.compile(r"slow|faster|%|\d\s*(?:ms|µs|us|s)\b", re.IGNORECASE)
COMMAND = re.compile(r"python3 (test/\S+\.py)|make check")


def agentJson(text: str) -> dict:
    """The findings object, out of the bare JSON or out of the CLI's envelope."""
    data = json.loads(text)
    if isinstance(data, dict) and "findings" not in data:
        if isinstance(data.get("structured_output"), dict):
            return data["structured_output"]
        block = re.search(r"\{.*\}", str(data.get("result", "")), re.DOTALL)
        data = json.loads(block[0]) if block else {}
    return data


def span(value: object, root: Path) -> tuple[str, list[str]]:
    """(why it is refused, the code it cites) — one of the two is empty."""
    if not isinstance(value, dict) or set(value) != {"file", "start", "end"}:
        return "a span is {file, start, end}", []
    file, start, end = value["file"], value["start"], value["end"]
    if not isinstance(file, str) or type(start) is not int or type(end) is not int:
        return "a span is {file: str, start: int, end: int}", []
    path = (root / file).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        return f"{file} is not a file of this repository", []
    size = len(path.read_text(errors="replace").splitlines())
    if not 1 <= start <= end <= size:
        return f"{file}:{start}-{end} is not inside the file, which has {size} lines", []
    return "", [text for n, text in meaningful(path) if start <= n <= end]


def refusal(f: object, root: Path) -> tuple[str, str]:
    """(why this finding is refused, its ID) — one of the two is empty."""
    if not isinstance(f, dict) or set(f) != {"kind", "title", "a", "b", "why", "delete"}:
        return "a finding is {kind, title, a, b, why, delete}", ""
    if f["kind"] not in KINDS:
        return f"kind is one of {KINDS}", ""
    for key, most in LIMITS.items():
        if not isinstance(f[key], str) or len(f[key]) > most:
            return f"`{key}` is a string of at most {most} characters", ""
    if not f["title"].strip() or not f["why"].strip():
        return "`title` and `why` say something", ""

    cited = []
    for side in ("a", "b") if f["b"] is not None else ("a",):
        reason, code = span(f[side], root)
        if reason:
            return reason, ""
        cited.append("\n".join(code))

    said = " ".join(f[key] for key in LIMITS).lower()
    if "sk-ant-" in said:
        return "it quotes something shaped like an API key", ""
    if f["b"] is not None and declared({f["a"]["file"], f["b"]["file"]}):
        return "the two files are a declared twin — test/twins.json", ""
    if word := next((w for w in REFUSED if w in said), ""):
        return f"it proposes an addition (`{word}`) — the rule here is deletion", ""

    if f["kind"] == "perf-question":
        if claim := SPEED_CLAIM.search(said):
            return f"it claims a speed (`{claim[0]}`) — the agent asks, the Mac measures", ""
        command = COMMAND.search(f["why"])
        if not command or (command[1] and not (root / command[1]).is_file()):
            return "a perf question ends with the command that answers it", ""
    elif not f["delete"].strip():
        return "`delete` names the lines to delete and what stays", ""

    # From the code, not from the line numbers: the same finding a week and
    # forty commits later is the same ID, and an issue closed once stays closed.
    return "", hashlib.sha256("\n--\n".join([f["kind"], *sorted(cited)]).encode()).hexdigest()[:12]


def validate(data: object, root: Path = Path()) -> tuple[list[dict], list[str]]:
    """What survives, and why the rest did not."""
    if not isinstance(data, dict) or not isinstance(data.get("findings"), list):
        return [], ['the answer is {"findings": [...]}']
    kept: list[dict] = []
    refused: list[str] = []
    for n, f in enumerate(data["findings"], 1):
        reason, identity = refusal(f, root)
        if not reason and identity in [k["id"] for k in kept]:
            reason = "it cites the same code as an earlier finding"
        if not reason and len(kept) == MOST:
            reason = f"only the first {MOST} leave"
        if reason:
            refused.append(f"finding {n}: {reason}")
        else:
            kept.append({"id": identity, **f})
    return kept, refused


def main() -> int:
    if len(sys.argv) < 2:
        print((__doc__ or "").strip().splitlines()[0])
        return 1
    try:
        data = agentJson(Path(sys.argv[1]).read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"{sys.argv[1]}: no JSON in it ({e})", file=sys.stderr)
        return 1
    kept, refused = validate(data)
    for line in refused:
        print(line, file=sys.stderr)
    out = json.dumps({"findings": kept}, indent=2, ensure_ascii=False) + "\n"
    if "-o" in sys.argv:
        Path(sys.argv[sys.argv.index("-o") + 1]).write_text(out)
        print(f"{len(kept)} finding(s) kept, {len(refused)} refused")
    else:
        print(out, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
