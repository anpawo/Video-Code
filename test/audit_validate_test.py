#!/usr/bin/env python3
"""
`test/audit_validate.py` against a recorded answer from the audit agent: one
finding worth reading, and the four ways an agent is wrong that must never
reach an issue.
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, "test")

from audit_validate import agentJson, validate  # noqa: E402
from helpers import check, section, summary  # noqa: E402

answer = agentJson(Path("test/audit/agent_output.json").read_text())
kept, refused = validate(answer)

section("A recorded answer")
check("read out of the CLI's envelope, code fence and all", len(answer["findings"]) == 5)
check("the good finding survives, alone", [k["title"] for k in kept] == [answer["findings"][0]["title"]])
check("it is a semantic clone — no similarity floor threw it out", kept[0]["a"]["file"] != kept[0]["b"]["file"])
check("a line range outside the file", "finding 2" in refused[0] and "not inside the file" in refused[0])
check("a declared twin", "finding 3" in refused[1] and "declared twin" in refused[1])
check("`extract a base class`", "finding 4" in refused[2] and "base class" in refused[2])
check("`30% slower`", "finding 5" in refused[3] and "claims a speed" in refused[3])

section("The same finding is the same ID")
moved = copy.deepcopy(answer["findings"][0])
moved["title"], moved["why"] = "reworded", "said differently"
check("whatever the agent calls it this week", validate({"findings": [moved]})[0][0]["id"] == kept[0]["id"])
check("and twice in one answer is once", len(validate({"findings": [answer["findings"][0], moved]})[0]) == 1)

section("What else does not leave")
good = answer["findings"][0]
perf = {**copy.deepcopy(answer["findings"][4]), "why": "Is this now done once per object? python3 test/perf/guard.py --record"}
check("a perf question that asks, and names its command, does", len(validate({"findings": [perf]})[0]) == 1)
check("one without a command", validate({"findings": [{**perf, "why": "Is this now done per object?"}]})[0] == [])
check("one that names a script that does not exist", validate({"findings": [{**perf, "why": "Per object? python3 test/perf/nope.py"}]})[0] == [])
check("a path out of the repository", validate({"findings": [{**good, "a": {"file": "../../etc/passwd", "start": 1, "end": 1}}]})[0] == [])
check("a field nobody asked for", validate({"findings": [{**good, "severity": "high"}]})[0] == [])
check("a duplicate that deletes nothing", validate({"findings": [{**good, "delete": ""}]})[0] == [])
check("an answer that is not the schema", validate([good]) == ([], ['the answer is {"findings": [...]}']))
check("silence is an answer", validate({"findings": []}) == ([], []))


def at(n: int) -> dict:
    return {**good, "a": {"file": "test/audit/seconds_b.py", "start": n, "end": 6}}


check("three at most, the first three", [k["a"]["start"] for k in validate({"findings": [at(1), at(4), at(5), at(6)]})[0]] == [1, 4, 5])

summary()
