#!/usr/bin/env python3

"""
Shared output helpers for all test/*_test.py files.
Provides colored check(), section(), and summary().
"""

from __future__ import annotations

import os
import sys

_R = "\033[0m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_CYAN = "\033[36m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_failures: list[str] = []
_skipped: list[str] = []


def needsRenderer(why: str) -> bool:
    """
    True when the compiled renderer is here, and a SAID skip when it is not.

    Two tests raised FileNotFoundError instead, so the fast CI lane — which does
    not build C++ on purpose, that is what makes it fast — went red on every
    push for a week and the whole suite was reported as broken. A test that
    cannot run is not a test that failed, but it must not be a test that stayed
    quiet either: the skip is printed, counted, and named in the summary.
    """
    if os.path.exists(os.path.abspath("video-code")):
        return True
    print(f"  {_DIM}—  skipped: {why} (no ./video-code — run `make` to include it){_R}")
    _skipped.append(why)
    return False


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
        print(f"{_GREEN}{_BOLD}All checks passed{_R}, {_DIM}{len(_skipped)} skipped for want of the renderer:{_R}")
        for k in _skipped:
            print(f"  {_DIM}— {k}{_R}")
    else:
        print(f"{_GREEN}{_BOLD}All checks passed.{_R}")
