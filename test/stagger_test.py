#!/usr/bin/env python3

"""
Assertion-based tests for `stagger`: the same effect on every member of a
group, one beat apart. Read off `Context.stack`, never off the objects.
Run directly: `python3 test/stagger_test.py`
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "test")
from helpers import check, section, summary

from videocode import *
from videocode.template.effect.other.popIn import popIn
from videocode.template.effect.other.stagger import stagger

EVERY = 0.1
BEAT = round(EVERY * FRAMERATE)


def frames(i: Input) -> dict[int, dict]:
    return {f: e for f, e in Context.stack[i.meta.index].items() if f != -1}


def opening(i: Input) -> int:
    """First frame `popIn` writes — construction leaves an `Align` at 0 on a letter."""
    return min(f for f, e in frames(i).items() if "Scale" in e)


def shifted(entries: dict[int, dict], by: int) -> dict[int, dict]:
    # `args.start` is the absolute frame, so it moves with the entry.
    return {
        f - by: {k: {**v, "args": {**v["args"], "start": v["args"]["start"] - by}} for k, v in e.items()}
        for f, e in entries.items()
    }


# ---------------------------------------------------------------------------
section("Group — same effect, opening one beat apart")

members = [Rectangle(width=1, height=1) for _ in range(3)]
Group(*members).apply(stagger(popIn(), every=EVERY))
check(f"members open {BEAT} frames apart", [opening(m) for m in members] == [0, BEAT, 2 * BEAT])
check("every member gets the SAME effect", all(shifted(frames(m), k * BEAT) == frames(members[0]) for k, m in enumerate(members)))
check("popIn reached the stack", "Scale" in frames(members[0])[0] and "Opacity" in frames(members[0])[0])

# ---------------------------------------------------------------------------
section("Text — one letter per beat")

txt = Text("abc", fontSize=0.5)
txt.apply(stagger(popIn(), every=EVERY))
check("letters open in order, one beat apart", [opening(l) for l in txt.inputs] == [0, BEAT, 2 * BEAT])

# ---------------------------------------------------------------------------
section("every=0 is the plain effect")

plain = [Rectangle(width=1, height=1) for _ in range(3)]
Group(*plain).apply(popIn())
zero = [Rectangle(width=1, height=1) for _ in range(3)]
Group(*zero).apply(stagger(popIn(), every=0))
check("stacks identical", [frames(m) for m in plain] == [frames(m) for m in zero])

# ---------------------------------------------------------------------------
section("the group's window covers the last member")

late = [Rectangle(width=1, height=1) for _ in range(3)]
g = Group(*late)
g.apply(stagger(popIn(duration=0.5), every=EVERY))
lastEnd = max(frames(late[-1])) + 1
check("last member ends after the first", lastEnd > max(frames(late[0])) + 1)
check("the scene's end is the last member's end", Context.lastEverAffectedFrame == lastEnd)
g.flush()
g.apply(opacity(128))
dimmed = [min(f for f, e in frames(m).items() if e.get("Opacity", {}).get("args", {}).get("opacity") == 128) for m in late]
check("a following group transform waits for the whole cascade", dimmed == [lastEnd] * 3)

summary()
