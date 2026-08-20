#!/usr/bin/env python3

"""
Rewriting one value in a scene, without disturbing the rest of it.

Every gesture in the editor is an edit to the source: dragging a clip's edge
changes an argument in the call that made it, moving an effect changes its
`start=`. That only works if a value can be replaced *exactly* — the call found
by where it is, the argument found by name, and the file otherwise byte for byte
what it was. Anything less and the buffer drifts away from what the person
wrote: reformatted lines, moved comments, a diff nobody can read.

So the source is parsed, never pattern-matched. Python's own `ast` carries the
line AND column of every node, and the edit is a splice of that span. What is
not the span is not touched — including the parts of the line either side of it.

    setArgument(src, line=5, call="Video", name="startFrame", value="120")
    setArgument(src, line=13, call="rotateBy", name="duration", value="1.5")

`call` picks one link out of a chain — `Group(a, b).rotateBy(180).scaleTo(0.5)`
is three calls on one line — and `occurrence` picks between repeats of the same
name. Nothing is guessed: a call that cannot be found returns the source
unchanged and says so, because a gesture that silently edits the wrong line is
worse than one that does nothing.
"""

from __future__ import annotations

import ast
from typing import NamedTuple


class Edit(NamedTuple):
    """The result of an edit: the new source, and whether anything happened."""

    source: str
    changed: bool
    message: str = ""


def _offsets(source: str) -> list[int]:
    """Character offset of the first character of each line (1-indexed lines)."""
    offsets = [0, 0]
    total = 0
    for line in source.splitlines(keepends=True):
        total += len(line)
        offsets.append(total)
    return offsets


def _span(source: str, node: ast.AST) -> tuple[int, int]:
    """The character range a node covers, in the whole source."""
    offsets = _offsets(source)
    start = offsets[node.lineno] + node.col_offset  # type: ignore[attr-defined]
    end = offsets[node.end_lineno] + node.end_col_offset  # type: ignore[attr-defined]
    return start, end


def _callName(node: ast.Call) -> str:
    """`Video` for `Video(...)`, `rotateBy` for `x.y.rotateBy(...)`."""
    target = node.func
    if isinstance(target, ast.Attribute):
        return target.attr
    if isinstance(target, ast.Name):
        return target.id
    return ""


def findCalls(source: str, line: int) -> list[str]:
    """
    Every call that starts on a line, in the order they are written.

    `Group(a, b).rotateBy(180).scaleTo(0.5)` gives `["Group", "rotateBy",
    "scaleTo"]` — what the editor offers when a gesture has to say which link of
    a chain it means.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    found: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.lineno <= line <= (node.end_lineno or node.lineno):
            found.append((node.lineno, node.col_offset, _callName(node)))

    # Written order, not walk order: a chain nests right-to-left in the tree and
    # the person reading the line goes left to right.
    return [name for _, _, name in sorted(found) if name]


def _pick(source: str, line: int, call: str, occurrence: int) -> ast.Call | None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    matches: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (node.lineno <= line <= (node.end_lineno or node.lineno)):
            continue
        if call and _callName(node) != call:
            continue
        matches.append(node)

    matches.sort(key=lambda n: (n.lineno, n.col_offset))
    if occurrence < 0 or occurrence >= len(matches):
        return None
    return matches[occurrence]


def readArgument(source: str, line: int, call: str, name: str, occurrence: int = 0) -> str | None:
    """
    What a keyword argument is currently written as, verbatim.

    The TEXT, not the value: `duration=1.5` gives `"1.5"`, and
    `easing=Easing.Out` gives `"Easing.Out"`. The editor shows and edits what
    was written, never its own idea of it.
    """
    node = _pick(source, line, call, occurrence)
    if node is None:
        return None

    for keyword in node.keywords:
        if keyword.arg == name:
            start, end = _span(source, keyword.value)
            return source[start:end]
    return None


def setArgument(
    source: str,
    line: int,
    call: str,
    name: str,
    value: str,
    occurrence: int = 0,
) -> Edit:
    """
    Set one keyword argument on one call, replacing its value or adding it.

    The value is written as given — it is source code, not data: `"1.5"`,
    `"Easing.Out"`, `"[(0, 30)]"` all go in as typed. Callers are the ones who
    know how a number should read.
    """
    node = _pick(source, line, call, occurrence)
    if node is None:
        return Edit(source, False, f"no call named {call!r} on line {line}")

    for keyword in node.keywords:
        if keyword.arg != name:
            continue
        start, end = _span(source, keyword.value)
        if source[start:end] == value:
            return Edit(source, False, "already that value")
        return Edit(source[:start] + value + source[end:], True)

    # Not there yet: written just inside the closing bracket, after whatever is
    # already in the call. The bracket is found from the end of the call rather
    # than by counting — a nested call's own bracket would be counted too.
    start, end = _span(source, node)
    closing = source.rfind(")", start, end)
    if closing < 0:
        return Edit(source, False, "unbalanced call")

    inner = source[start:closing]
    hasArguments = bool(node.args or node.keywords)
    separator = ", " if hasArguments and not inner.rstrip().endswith("(") else ""
    return Edit(source[:closing] + separator + f"{name}={value}" + source[closing:], True)


def argumentSpan(
    source: str,
    line: int,
    call: str,
    name: str,
    value: str,
    occurrence: int = 0,
) -> tuple[int, int, str] | None:
    """
    The same edit as `setArgument`, expressed as a range and what to put in it.

    Replacing `source[start:end]` with the text gives the edited file. The
    editor needs this rather than the finished string because a gesture that
    hands the pane a whole new buffer erases the pane's undo history — Qt
    records edits, not assignments, and ⌘Z after a drag did nothing. Applied as
    a remove-and-insert on the document, the gesture lands in the same history
    as typing, and one ⌘Z takes it back.

    `None` when the call is not there, which is a refusal, not an empty edit.
    """
    node = _pick(source, line, call, occurrence)
    if node is None:
        return None

    for keyword in node.keywords:
        if keyword.arg != name:
            continue
        start, end = _span(source, keyword.value)
        if source[start:end] == value:
            return None
        return start, end, value

    start, end = _span(source, node)
    closing = source.rfind(")", start, end)
    if closing < 0:
        return None

    inner = source[start:closing]
    hasArguments = bool(node.args or node.keywords)
    separator = ", " if hasArguments and not inner.rstrip().endswith("(") else ""
    return closing, closing, f"{separator}{name}={value}"


def removeArgument(source: str, line: int, call: str, name: str, occurrence: int = 0) -> Edit:
    """
    Take a keyword argument out, and the separator that came with it.

    Used when a gesture returns a value to its default: writing `duration=0.4`
    when 0.4 is what the signature already says is noise the next reader has to
    check against the docs.
    """
    node = _pick(source, line, call, occurrence)
    if node is None:
        return Edit(source, False, f"no call named {call!r} on line {line}")

    for index, keyword in enumerate(node.keywords):
        if keyword.arg != name:
            continue

        start = _span(source, keyword.value)[0]
        # Back up over `name=` and, if this is not the first argument, over the
        # comma and space in front of it.
        start = source.rfind(name, 0, start)
        _, end = _span(source, keyword.value)

        before = source[:start].rstrip()
        if before.endswith(","):
            start = len(before) - 1
        elif index == 0 and source[end:].lstrip().startswith(","):
            end = source.index(",", end) + 1
            if source[end : end + 1] == " ":
                end += 1

        return Edit(source[:start] + source[end:], True)

    return Edit(source, False, f"no argument named {name!r}")


def callLine(source: str, name: str, occurrence: int = 0) -> int:
    """
    Where a call is, for a caller that knows the name but not the line.

    Answers 0 when there is none, which is not a line number — every real line
    is 1 or more.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0

    matches = sorted(
        (node.lineno, node.col_offset)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _callName(node) == name
    )
    if occurrence < 0 or occurrence >= len(matches):
        return 0
    return matches[occurrence][0]
