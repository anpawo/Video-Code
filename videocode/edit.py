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
from typing import NamedTuple, Sequence


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


def _chars(source: str, lineno: int, byteCol: int) -> int:
    """
    A column as `ast` reports it — UTF-8 BYTES — as a count of characters.

    `col_offset` is documented in bytes, and the rest of this file counts
    characters, so an accent earlier on the line pushes every span one too far
    right: `Text("Bonjour à tous", fontSize=1)` had its closing bracket eaten
    and the scene stopped parsing. The person writes French; the first `Text`
    any gesture touched broke.

    Characters, not UTF-16 units — that is this conversion's ceiling. QML's
    document positions are UTF-16, so a character above the BMP (an emoji)
    earlier on the same line is still off by one in the editor. The place for
    that second conversion is `src/window/Editor.cpp`, where the span is
    applied to the document; it is not needed for accents.
    """
    offsets = _offsets(source)
    line = source[offsets[lineno] : offsets[lineno + 1]]
    return len(line.encode("utf-8")[:byteCol].decode("utf-8", "ignore"))


def _span(source: str, node: ast.AST) -> tuple[int, int]:
    """The character range a node covers, in the whole source."""
    offsets = _offsets(source)
    start = offsets[node.lineno] + _chars(source, node.lineno, node.col_offset)  # type: ignore[attr-defined]
    end = offsets[node.end_lineno] + _chars(source, node.end_lineno, node.end_col_offset)  # type: ignore[attr-defined]
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


def _isNumber(node: ast.expr) -> bool:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        node = node.operand
    return isinstance(node, ast.Constant) and type(node.value) in (int, float)


def _kept(source: str, node: ast.expr, value: str) -> str:
    """
    Why the value already written has to stay, or "" when it may be replaced.

    `wait(PAUSE_DELAY)` says something `wait(0.4)` does not: that the pause is
    one decision, made once and shared by thirty lines. A drag that writes `0.5`
    over the name keeps the timing and loses the decision — silently, since the
    scene still runs. So a number may only replace a number. A name or an
    expression is the person's, and the gesture says so rather than doing
    nothing: a refusal nobody hears looks exactly like a gesture that failed.
    """
    try:
        float(value)
    except ValueError:
        return ""
    if _isNumber(node):
        return ""

    start, end = _span(source, node)
    text = source[start:end]
    if isinstance(node, ast.Name):
        return f"{text} is a name, not a number — change {text} itself"
    return f"{text} is written as an expression — edit the line itself"


def constantOffer(
    source: str,
    line: int,
    call: str,
    key: str | int,
    value: str,
    occurrence: int = 0,
) -> tuple[str, int, int, str, int] | None:
    """
    The name a gesture was refused for, and where that name's own value is written.

    A refusal that only says no leaves the person to go and find
    `PAUSE_DELAY = 0.4` themselves — and the edit they wanted is one character
    away from the one they are allowed to make. So the shell can offer the other
    one: the constant's own line, with the number of places that read it, because
    changing it changes all of them and that is the whole reason it has a name.

    `key` is the keyword's name, or the index of a positional. `None` unless the
    argument really is a plain name assigned a plain number at the top level of
    this file — anything cleverer is a decision no gesture should be making.
    """
    node = _pick(source, line, call, occurrence)
    if node is None:
        return None

    target: ast.expr | None = None
    if isinstance(key, int):
        if key < len(node.args):
            target = node.args[key]
    else:
        for keyword in node.keywords:
            if keyword.arg == key:
                target = keyword.value
    if not isinstance(target, ast.Name):
        return None

    try:
        float(value)
    except ValueError:
        return None

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    for statement in tree.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        assigned = statement.targets[0]
        if not isinstance(assigned, ast.Name) or assigned.id != target.id:
            continue
        if not _isNumber(statement.value):
            continue
        start, end = _span(source, statement.value)
        uses = sum(
            1
            for found in ast.walk(tree)
            if isinstance(found, ast.Name) and found.id == target.id and isinstance(found.ctx, ast.Load)
        )
        return target.id, start, end, value, uses
    return None


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
        if reason := _kept(source, keyword.value, value):
            return Edit(source, False, reason)
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
) -> tuple[int, int, str] | str | None:
    """
    The same edit as `setArgument`, expressed as a range and what to put in it.

    Replacing `source[start:end]` with the text gives the edited file. The
    editor needs this rather than the finished string because a gesture that
    hands the pane a whole new buffer erases the pane's undo history — Qt
    records edits, not assignments, and ⌘Z after a drag did nothing. Applied as
    a remove-and-insert on the document, the gesture lands in the same history
    as typing, and one ⌘Z takes it back.

    `None` when the call is not there, which is a refusal, not an empty edit. A
    sentence when the value written is one the gesture may not replace — see
    `_kept` — because that refusal is one the person has to hear.
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
        return _kept(source, keyword.value, value) or (start, end, value)

    start, end = _span(source, node)
    closing = source.rfind(")", start, end)
    if closing < 0:
        return None

    inner = source[start:closing]
    hasArguments = bool(node.args or node.keywords)
    separator = ", " if hasArguments and not inner.rstrip().endswith("(") else ""
    return closing, closing, f"{separator}{name}={value}"


def positionalSpan(
    source: str,
    line: int,
    call: str,
    index: int,
    value: str,
    occurrence: int = 0,
) -> tuple[int, int, str] | str | None:
    """
    The same as `argumentSpan`, for an argument that has no name.

    `wait(0.3)` is the case that asked for it: the number is written in the
    brackets, not after an `=`, and a timeline that lets you drag a gap has to
    rewrite exactly that. Missing arguments are appended in order — `wait()`
    takes a first positional the way `wait(0.3)` already has one. The same
    sentence as `argumentSpan` when what is written is not the gesture's to
    replace: `wait(PAUSE_DELAY)` keeps its name.
    """
    node = _pick(source, line, call, occurrence)
    if node is None:
        return None

    if index < len(node.args):
        start, end = _span(source, node.args[index])
        if source[start:end] == value:
            return None
        return _kept(source, node.args[index], value) or (start, end, value)

    # Only the argument straight after the last one written can be added: there
    # is no way to skip a slot without naming it, and guessing a name here would
    # be inventing part of a signature.
    if index != len(node.args) or node.keywords:
        return None

    start, end = _span(source, node)
    closing = source.rfind(")", start, end)
    if closing < 0:
        return None

    separator = ", " if node.args else ""
    return closing, closing, f"{separator}{value}"


def readPositional(source: str, line: int, call: str, index: int, occurrence: int = 0) -> str | None:
    """
    What an argument written WITHOUT a name says, verbatim.

    `Video("shot.mp4")` keeps its file in the first slot, and the editor has to
    be able to read it back: dragging that clip from the bin onto the timeline
    writes another call about the same file, and the file is only ever named
    here. The TEXT again — `"shot.mp4"` with its quotes, or `PATH` if that is
    what was typed — because what goes back into a call is what came out of one.
    """
    node = _pick(source, line, call, occurrence)
    if node is None or index >= len(node.args):
        return None

    start, end = _span(source, node.args[index])
    return source[start:end]


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


def removeCallSpan(
    source: str,
    line: int,
    call: str,
    occurrence: int = 0,
) -> tuple[int, int, str] | None:
    """
    The span that takes a call away, as a range to replace with nothing.

    Two shapes, told apart by what is left behind:

    - a link in a chain — `Group(a, b).scaleTo(0.5).rotateBy(180)` — where only
      `.scaleTo(0.5)` goes, from the end of what it was called on to its own end;
    - a statement of its own — `square.fadeIn()` — where removing the link would
      leave the bare name `square` sitting on a line, so the line goes with it,
      newline included.

    `None` when the call is not there, or when it is nested inside something
    else (an argument, an assignment's value): taking it out then changes what
    the surrounding expression means, and a gesture may not do that quietly.
    """
    node = _pick(source, line, call, occurrence)
    if node is None:
        return None

    start, end = _span(source, node)

    # Where the link begins: just after whatever it was called on.
    if not isinstance(node.func, ast.Attribute):
        receiverEnd = start
    else:
        receiverEnd = _span(source, node.func.value)[1]

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    # The statement this call sits in, and whether the call IS all of it.
    for statement in ast.walk(tree):
        if not isinstance(statement, ast.Expr):
            continue
        if _span(source, statement) != (start, end) and _span(source, statement.value) != (start, end):
            continue

        # Only when nothing else on the line does anything. `square.fadeIn()`
        # leaves a bare name behind, so the line goes; but the last link of
        # `Group(a, b).scaleTo(0.5).rotateBy(180)` is also the outermost call,
        # and taking its line would take the scale with it.
        if any(isinstance(inner, ast.Call) for inner in ast.walk(node.func)):
            break

        offsets = _offsets(source)
        lineStart = offsets[statement.lineno]
        lineEnd = offsets[(statement.end_lineno or statement.lineno) + 1] if (statement.end_lineno or statement.lineno) + 1 < len(offsets) else len(source)
        if source[lineStart:_span(source, statement)[0]].strip() == "":
            return lineStart, lineEnd, ""

    # A link in a chain, and only a link.
    if receiverEnd == start:
        return None
    return receiverEnd, end, ""


def waitLinkSpan(
    source: str,
    line: int,
    calls: Sequence[str],
    seconds: float,
) -> tuple[int, int, str] | str | None:
    """
    The span that makes what a line starts happen `seconds` later — or sooner.

    Dragging a clip along the timeline moves the element's OWN clock, and the
    word for that is `.wait()`:

        title = Text("Bonjour").fadeIn()            # dragged 0.5 s to the right
        title = Text("Bonjour").wait(0.5).fadeIn()

    `calls` are the links on that line that take time; the wait belongs in
    front of the leftmost of them. Not straight after the constructor:
    `Square().wait(1).opacity(0)` leaves the square fully opaque for the second
    it was meant to be absent. Not at the end of the chain either: links of one
    chain share a clock until a `flush()`, so a wait after `.fadeIn()` delays
    nothing that is already written.

    A `.wait(n)` already standing there is the same decision made earlier, so
    its number changes instead of a second link appearing — and at zero the link
    goes, because `.wait(0)` is a sentence that says nothing.

    A sentence when the gesture may not do it: the wait is a name (see `_kept`),
    or there is less wait than the drag asks back. `None` when the line holds no
    such chain.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    chain: list[ast.Call] = []
    for statement in ast.walk(tree):
        if not isinstance(statement, (ast.Expr, ast.Assign, ast.AnnAssign)):
            continue
        if not (statement.lineno <= line <= (statement.end_lineno or statement.lineno)):
            continue
        node = statement.value
        while isinstance(node, ast.Call):
            chain.append(node)
            node = node.func.value if isinstance(node.func, ast.Attribute) else None
        break

    # Walked from the outside in, read from the left: the last one found is the
    # first one written.
    target = next((link for link in reversed(chain) if isinstance(link.func, ast.Attribute) and link.func.attr in calls), None)
    if target is None or not isinstance(target.func, ast.Attribute):
        return None

    held = target.func.value
    if isinstance(held, ast.Call) and isinstance(held.func, ast.Attribute) and held.func.attr == "wait" and len(held.args) == 1:
        written = held.args[0]
        if reason := _kept(source, written, "0"):
            return reason

        old = float(ast.literal_eval(written))
        new = round(old + seconds, 2)
        # Dragged back to where it would stand with no wait at all, a clip
        # overshoots by a frame or two — a fade is first SEEN one frame after
        # it starts, and the edge snaps to what is seen. That is the gesture
        # for "no wait", not a request for more than there is.
        if -0.1 <= new < 0:
            new = 0
        if new < 0:
            return f"nothing but {old:g}s of .wait() to give back on line {line} — what else holds it there is written above"
        if new == 0:
            return _span(source, held.func.value)[1], _span(source, held)[1], ""
        start, end = _span(source, written)
        return start, end, f"{new:g}"

    if round(seconds, 2) <= 0:
        return f"nothing to shorten: no .wait() in front of {target.func.attr}() — what holds it there is written above line {line}"

    at = _span(source, held)[1]
    return at, at, f".wait({round(seconds, 2):g})"


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
