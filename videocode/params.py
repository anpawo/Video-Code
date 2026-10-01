#!/usr/bin/env python3

"""
Scene parameters: one scene written as a template, filled from outside.

    name  = param("name", "World")     # a str
    score = param("score", 0)          # "12" arrives as 12
    brand = param("brand", BLUE)       # "#ff8800" arrives as an rgba
    title = param("title")             # no default: it must be given

    ./video-code --file card.py --generate card.mp4 --set name=Ada --set score=12
    ./video-code --file card.py --generate "out/{name}.mp4" --data people.csv

Before this, the only thing that reached a scene from outside was VC_SCREEN.
Generating videos automatically — the README's second goal — is one scene and
N rows of values, N files. Remotion's input props: `defaultProps` on the
composition, `--props` overriding them. Remotion has no command for a dataset,
though: its docs hand you a Node loop around `renderMedia()`. Here `--data` is
that loop.

The values travel like the resolution does: C++ exports VC_PARAMS (JSON)
before each run, and `param()` reads it at the moment it is called — never at
import — so rows can follow each other in one process.

Nothing here imports the rest of `videocode` at load time: C++ calls `plan()`
before a render, and the world box must be built from the resolution the
render was given, not from whatever VC_SCREEN said when this was first
imported. `rgba` is fetched when a colour is actually asked for.
"""

from __future__ import annotations

import csv
import json
import os
import re
import string
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar, overload

T = TypeVar("T")

__all__ = ["param"]


class ParamError(ValueError):
    """A parameter that is missing, unreadable, or given to a scene that never reads it."""


# What the current run was given, as C++ exported it: {"values": {...}, "set":
# [keys typed with --set], "from": "rows.csv, row 3"}. Parsed once per distinct
# string — a scene reads a parameter inside a loop as easily as outside one.
_given: tuple[str, dict] = ("", {})

# The names the current run asked for, and the columns no run has asked for
# yet — `unreadColumns()` is said once, after the last row.
_asked: set[str] = set()
_columnsNeverRead: set[str] | None = None

_MISSING: Any = object()


def _received() -> dict:
    global _given
    raw = os.environ.get("VC_PARAMS", "")
    if raw != _given[0]:
        _given = (raw, json.loads(raw) if raw else {})
    return _given[1]


@overload
def param(name: str) -> str: ...
@overload
def param(name: str, default: T) -> T: ...
def param(name: str, default: Any = _MISSING) -> Any:
    """
    The value given for `name` by `--set name=value` or a `--data` column,
    else `default`.

    The default's type is the parameter's type: a CSV cell is always text, so
    `param("score", 0)` turns "12" into 12, `param("on", False)` reads
    true/false/yes/no/1/0, and `param("brand", BLUE)` reads "#ff8800". A value
    that does not read as that type is refused, naming the row it came from,
    rather than handed on as a string that breaks three calls later.

    Without a default the parameter is required and read as text. The editor
    runs a scene with nothing given, so a parameter with a default keeps the
    template previewable; one without stops it with a message saying what to
    pass.
    """
    _asked.add(name)
    given = _received()
    values = given.get("values", {})
    # "--set score='abc' is not…", "people.csv, row 3: score='abc' is not…"
    where = given.get("from", "--set")
    where += " " if where == "--set" else ": "

    if name not in values:
        if default is _MISSING:
            raise ParamError(
                f"param({name!r}) has no default and was not given — pass --set {name}=… or a --data "
                f"column named {name!r}, or give it a default: param({name!r}, …)."
            )
        return default

    raw = values[name]
    if default is _MISSING or default is None:
        return raw if isinstance(raw, str) else json.dumps(raw)
    try:
        return _as(raw, default)
    except (ValueError, TypeError, KeyError, IndexError):
        raise ParamError(
            f"{where}{name}={raw!r} is not {_kind(default)}, the type of param({name!r})'s default."
        ) from None


def _as(raw: Any, default: Any) -> Any:
    """`raw` — text from a CSV or --set, or a JSON value — read as `default`'s type."""
    kind = type(default)
    if isinstance(default, bool):
        if isinstance(raw, bool):
            return raw
        said = str(raw).strip().lower()
        if said in ("true", "yes", "on", "1"):
            return True
        if said in ("false", "no", "off", "0"):
            return False
        raise ValueError(raw)
    if isinstance(default, int):
        if isinstance(raw, float) and raw.is_integer():
            return int(raw)
        if isinstance(raw, (bool, float)):
            raise ValueError(raw)
        return int(raw)
    if isinstance(default, float):
        if isinstance(raw, bool):
            raise ValueError(raw)
        return float(raw)
    if isinstance(default, str):
        return raw if isinstance(raw, str) else json.dumps(raw)
    if isinstance(default, Enum):
        # By name first — `Align.LEFT` is written `LEFT` — then by value.
        members = type(default)
        try:
            return members[str(raw).strip()]
        except KeyError:
            return members(raw)

    from videocode.color import rgba

    if isinstance(default, rgba):
        said = str(raw).strip().lstrip("#")
        if not re.fullmatch(r"[0-9a-fA-F]{6}([0-9a-fA-F]{2})?", said):
            raise ValueError(raw)
        return rgba("#" + said)
    if isinstance(raw, kind):
        return raw
    return kind(raw)


def _kind(default: Any) -> str:
    from videocode.color import rgba

    if isinstance(default, bool):
        return "true or false"
    if isinstance(default, int):
        return "a whole number"
    if isinstance(default, float):
        return "a number"
    if isinstance(default, rgba):
        return 'a colour like "#ff8800"'
    if isinstance(default, Enum):
        return "one of " + ", ".join(m.name for m in type(default))
    return f"a {type(default).__name__}"


def startRun() -> None:
    """Forget what the last run asked for. Called by `_resetContext`."""
    _asked.clear()


def checkRun() -> None:
    """
    After a run: a `--set` key that no `param()` read is an error — a typo
    would render the default, silently, on every file of the batch. A `--data`
    column is only noted here, and said once at the end if no row read it: a
    CSV often carries columns that are there for the filename, or for nobody.
    """
    global _columnsNeverRead
    given = _received()
    if not given:
        return
    typed = sorted(set(given.get("set", [])) - _asked)
    if typed:
        asked = ", ".join(sorted(_asked)) or "nothing"
        raise ParamError(
            f"--set {', '.join(typed)}: the scene has no param() of that name (it reads {asked}). "
            f"A misspelt name would otherwise render the default."
        )
    columns = set(given.get("values", {})) - set(given.get("set", []))
    if columns:
        _columnsNeverRead = (columns if _columnsNeverRead is None else _columnsNeverRead) - _asked


def unreadColumns() -> str:
    """The `--data` columns no row's run read, as the line to print — empty when every one was."""
    global _columnsNeverRead
    unread, _columnsNeverRead = sorted(_columnsNeverRead or ()), None
    if not unread:
        return ""
    return f"video-code: warning: no param() read the --data column{'s' if len(unread) > 1 else ''} {', '.join(unread)}.\n"


# ── The batch, before anything renders ─────────────────────────────────────


def _readData(path: str) -> list[dict]:
    """
    The rows of a .csv (a header line, then one render per line) or a .json (a
    list of objects, or one object). An empty CSV cell is a value not given,
    so the scene's default applies — a spreadsheet leaves blanks, and a blank
    is not an empty title.
    """
    file = Path(path)
    if not file.is_file():
        raise ParamError(f"--data: cannot read {path}.")
    if file.suffix.lower() == ".json":
        data = json.loads(file.read_text(encoding="utf-8"))
        rows = [data] if isinstance(data, dict) else data
        if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
            raise ParamError(f"--data {path}: a JSON file must hold an object, or a list of objects — one per render.")
        return rows
    if file.suffix.lower() != ".csv":
        raise ParamError(f"--data {path}: reads a .csv or a .json file.")
    # utf-8-sig: a CSV saved by Excel starts with a byte-order mark, which would
    # otherwise become part of the first column's name.
    with file.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header = [h.strip() for h in (reader.fieldnames or [])]
        if not header or any(not h for h in header):
            raise ParamError(f"--data {path}: the first line must name every column.")
        rows = []
        for line in reader:
            if None in line:
                raise ParamError(f"--data {path}:{reader.line_num}: more cells than the header has columns.")
            rows.append({k.strip(): v for k, v in line.items() if v is not None and v != ""})
    if not rows:
        raise ParamError(f"--data {path}: a header and no rows — nothing to render.")
    return rows


def _fileSafe(value: Any) -> str:
    """A cell as a piece of a filename: no folder separators, no characters a shell or Windows chokes on."""
    text = value if isinstance(value, str) else json.dumps(value)
    return re.sub(r'[\\/:*?"<>|\s]+', "-", text.strip()).strip("-.") or "_"


def _fields(template: str) -> list[str]:
    return [field for _, field, _, _ in string.Formatter().parse(template) if field is not None]


def plan(sets: list[str], data: str, output: str) -> list[dict]:
    """
    One entry per render — `{"params": <VC_PARAMS JSON>, "output": path,
    "note": "row 3 of 12"}` — worked out, and checked, before the first frame:

    - `--set key=value`, repeatable, for a single render or on top of every row;
    - `--data rows.csv|json`, one render per row;
    - `--generate "out/{name}.mp4"` names each file from its row; without a
      `{column}` a batch numbers its files (`out-1.mp4`, `out-2.mp4`…).

    Refused here, rather than half way through a batch: a key given by both
    `--set` and `--data`, a `{field}` that names no column, two rows that
    would write the same file.
    """
    typed: dict[str, str] = {}
    for item in sets:
        key, eq, value = item.partition("=")
        key = key.strip()
        if not eq or not key:
            raise ParamError(f"--set wants key=value, got {item!r}.")
        if key in typed:
            raise ParamError(f"--set {key} is given twice.")
        typed[key] = value

    rows = _readData(data) if data else [{}]
    source = Path(data).name if data else ""
    if data:
        both = sorted(set(typed) & {k for row in rows for k in row})
        if both:
            raise ParamError(f"--set {', '.join(both)} is also a column of {source} — say it in one place, not two.")

    fields = _fields(output)
    batch = len(rows) > 1
    renders: list[dict] = []
    for i, row in enumerate(rows, 1):
        values = {**row, **typed}
        if fields:
            missing = [f for f in fields if f not in values]
            if missing:
                raise ParamError(
                    f"--generate {output} names {{{missing[0]}}}, which "
                    + (f"row {i} of {source} leaves empty." if any(missing[0] in r for r in rows)
                       else "is neither a --set key nor a --data column.")
                )
            path = output.format_map({k: _fileSafe(v) for k, v in values.items()})
        elif batch:
            out = Path(output)
            path = str(out.with_name(f"{out.stem}-{i}{out.suffix}"))
        else:
            path = output
        where = f"{source}, row {i}" if data else "--set"
        renders.append({
            "params": json.dumps({"values": values, "set": sorted(typed), "from": where}),
            "output": path,
            "note": f"row {i} of {len(rows)}" if batch else "",
        })

    seen: dict[str, int] = {}
    for i, render in enumerate(renders, 1):
        if render["output"] in seen:
            raise ParamError(
                f"--generate {output}: rows {seen[render['output']]} and {i} would both write {render['output']}. "
                f"Name the files by a column that differs, or leave the {{}} out to number them."
            )
        seen[render["output"]] = i

    # "out/{team}/{name}.mp4" makes its folders as it goes — one per team is
    # not something to create by hand first. Only now, once nothing is refused.
    for render in renders:
        Path(render["output"]).parent.mkdir(parents=True, exist_ok=True)
    return renders


def provide(params: str) -> None:
    """Point the next run at one entry of `plan()` — C++ calls this before each render."""
    os.environ["VC_PARAMS"] = params
