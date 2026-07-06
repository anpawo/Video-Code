#!/usr/bin/env python3

from __future__ import annotations

from videocode.ty import *


__all__ = ["TrackedPath"]


class TrackedPath:
    """
    Per-frame world-space positions produced by `Video.track()` — a sparse
    point track: `{sourceFrameIndex: (worldX, worldY)}`.

    Frame indices live in the SOURCE video's raw frame-index space (see
    `Video.track()`'s docstring for the `cuts`/`speedRamps` caveat), and
    positions are already converted to world-space units — consumers never
    need to know anything about pixels or the source resolution.

    Deliberately dependency-free (only `videocode.ty`) so both `Video`
    (which builds it) and `Input` (which consumes it via `attachTo()`) can
    import it without a circular import.
    """

    def __init__(self, positions: dict[frame, point]) -> None:
        self.positions = positions

    def __len__(self) -> int:
        return len(self.positions)

    def __iter__(self):
        return iter(sorted(self.positions.items()))

    def __getitem__(self, sourceFrameIndex: frame) -> point:
        return self.positions[sourceFrameIndex]

    def __contains__(self, sourceFrameIndex: object) -> bool:
        return sourceFrameIndex in self.positions
