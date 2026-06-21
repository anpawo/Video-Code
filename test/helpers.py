#!/usr/bin/env python3

"""
Shared output helpers for all test/*_test.py files.
Provides colored check(), section(), and summary().
"""

from __future__ import annotations

import sys

_R = "\033[0m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_CYAN = "\033[36m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_failures: list[str] = []


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
    else:
        print(f"{_GREEN}{_BOLD}All checks passed.{_R}")
