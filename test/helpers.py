#!/usr/bin/env python3

"""
Shared output helpers for all test/*_test.py files.
Provides colored check(), section(), and summary().
"""

from __future__ import annotations

import os
import shutil
import sys

_R = "\033[0m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_CYAN = "\033[36m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_failures: list[str] = []
_skipped: list[str] = []


def needsTool(tool: str, why: str) -> bool:
    """
    True when an external tool is on this machine, and a SAID skip when it is not.

    Three tests raised FileNotFoundError instead — for the renderer binary, for
    `ffmpeg`, for `latex` — so the fast CI lane, which installs none of them on
    purpose because that is what makes it fast, reported "2 of 44 FAILED" and a
    whole suite looked broken. A test that CANNOT RUN is not a test that failed.

    It must not be a test that stayed quiet either, which is the other half of
    the same disease: the skip is printed, counted, and named in the summary, so
    a lane that quietly stopped covering something says so out loud.
    """
    found = os.path.exists(os.path.abspath(tool)) if tool.startswith("./") else shutil.which(tool)
    if found:
        return True
    print(f"  {_DIM}—  skipped: {why} (no `{tool}` here){_R}")
    _skipped.append(f"{why} — needs {tool}")
    return False


def needsRenderer(why: str) -> bool:
    """The compiled renderer, which is a tool like any other."""
    return needsTool("./video-code", why)


def section(title: str) -> None:
    print(f"\n{_CYAN}{_BOLD}{title}{_R}")


def check(label: str, condition: bool) -> None:
    if condition:
        print(f"  {_GREEN}✓{_R}  {label}")
    else:
        print(f"  {_RED}✗{_R}  {_BOLD}{label}{_R}")
        _failures.append(label)


def summary() -> None:
    print()
    if _failures:
        print(f"{_RED}{_BOLD}{len(_failures)} FAILURE(S):{_R}")
        for f in _failures:
            print(f"  {_RED}•{_R} {f}")
        sys.exit(1)
    elif _skipped:
        print(f"{_GREEN}{_BOLD}All checks passed{_R}, {_DIM}{len(_skipped)} skipped for want of a tool:{_R}")
        for k in _skipped:
            print(f"  {_DIM}— {k}{_R}")
    else:
        print(f"{_GREEN}{_BOLD}All checks passed.{_R}")
