#!/usr/bin/env python3

from __future__ import annotations

import subprocess

from videocode.input.shape.Polygon import *
from videocode.constants import WORLD_TO_SCREEN_RATIO
from videocode.input.media.TrackedPath import TrackedPath


__all__ = ["Video", "TrackedPath"]


def _pixelToWorld(
    px: number, py: number,
    srcW: number, srcH: number,
    width: number, height: number,
    centerX: number, centerY: number,
) -> point:
    """
    Pure coordinate-conversion math backing `Video.track()` — factored out
    so it's testable without decoding any actual video. See `Video.track()`'s
    docstring for the full derivation; in short:

    `(px, py) / (srcW, srcH)` is a 0..1 fraction across the source frame.
    `position()` places the shape's bbox CENTER at `(centerX, centerY)` under
    the default `align=(0.5, 0.5)`, and world Y is positive-upward while
    image Y is positive-downward (X is not flipped), so:

        worldX = centerX + width  * (px / srcW - 0.5)
        worldY = centerY + height * (0.5 - py / srcH)
    """
    worldX = centerX + width * (px / srcW - 0.5)
    worldY = centerY + height * (0.5 - py / srcH)
    return (worldX, worldY)


class Video(Polygon):
    cppName = "Video"
    cppAttrs = Polygon.cppAttrs | {"filepath", "cuts", "speedRamps", "uvMapping", "uvAngle"}

    def __init__(
        self,
        filepath: str,
        cuts: list[frame | tuple[frame, frame]] = [],
        startFrame: frame = 0,
        endFrame: maybe[frame] = None,
        speedRamps: list[tuple[frame, frame, float]] = [],
        width: maybe[wunumber] = None,
        height: maybe[wunumber] = None,
        cornerRadius: percent = 0,
        strokeColor: rgba = TRANSPARENT,
        strokeWidth: wufloat = 0,
        uvMapping: UVMapping = UVMapping.STRETCH,
        uvAngle: wufloat = 0,
    ) -> None:
        """
        `cuts` are ranges of source-video frames to skip during playback —
        either a single frame index `n` (shorthand for `(n, n + 1)`) or a
        `(start, end)` pair cutting `[start, end)`.

        `startFrame`/`endFrame` restrict playback to the source frame range
        `[startFrame, endFrame)` — shorthand for cutting everything outside
        that range (`endFrame=None` plays to the end of the source).

        `speedRamps` are `(playbackStart, playbackEnd, rate)` triples that
        retime playback over a `[playbackStart, playbackEnd)` window —
        **playback-frame space**, i.e. the same post-cut index space
        `startFrame`/`endFrame` and the rest of the cut-down timeline already
        use, not raw source-file frame numbers. Within that window the source
        index advances at `rate` source-frames per playback-frame instead of
        the implicit 1x:

        - `1.0` (or no ramp covering a given frame): unchanged playback.
        - `> 1.0` (e.g. `2.0`): sped up — the source advances faster than
          playback, so more source footage passes in the same playback span.
        - `0.0 < rate < 1.0` (e.g. `0.5`): slow motion.
        - `0.0`: freeze-frame — the source index holds at the frame it was
          at when the window started.
        - negative (e.g. `-1.0`): reverse playback — the source index
          decreases as playback advances.

        Frame sampling is nearest-frame (no frame-blending) at every rate —
        matching the fact that there's no blend/lerp step anywhere else in
        `Video`'s frame pipeline; smooth interpolation for non-1x rates is a
        possible future enhancement, not implemented here.

        Ramp windows must be non-overlapping (in playback-frame space) —
        overlapping ramps raise a `ValueError`. A ramp window may cross a
        `cuts`/`startFrame`/`endFrame` boundary, but a cut boundary *inside*
        a non-1x ramp window isn't specially accounted for by the ramp's own
        rate math (only by where the ramp's source anchor sits) — ramps
        aren't expected to straddle a cut in practice.

        `uvMapping` controls how the texture is wrapped onto the shape —
        see the `UVMapping` enum for the mode semantics; `uvAngle` (degrees)
        rotates the angular origin of the polar modes.
        """
        self.filepath = filepath
        self.uvMapping = uvMapping
        self.uvAngle = uvAngle
        cuts = [c if isinstance(c, tuple) else (c, c + 1) for c in cuts]
        if startFrame:
            cuts.append((0, startFrame))
        if endFrame is not None:
            # the C++ side clamps `end` to the source's actual frame count,
            # so an over-large sentinel cuts everything past `endFrame`.
            cuts.append((endFrame, 2**31 - 1))
        self.cuts = cuts

        speedRamps = sorted(speedRamps, key=lambda ramp: ramp[0])
        for (aStart, aEnd, _), (bStart, bEnd, _) in zip(speedRamps, speedRamps[1:]):
            if bStart < aEnd:
                raise ValueError(
                    "Video speedRamps must be non-overlapping in playback space, "
                    f"got overlapping segments ({aStart}, {aEnd}) and ({bStart}, {bEnd})"
                )
        self.speedRamps = speedRamps

        # Rounding/stroking needs a known shape — if the caller didn't give
        # one, fall back to the video's natural frame size (ffprobe metadata,
        # no frame decode).
        if cornerRadius and width is None and height is None:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height", "-of", "csv=p=0", filepath],
                capture_output=True, text=True, check=True,
            )
            w, h = out.stdout.strip().split(",")
            width = float(w) / WORLD_TO_SCREEN_RATIO
            height = float(h) / WORLD_TO_SCREEN_RATIO

        self.width = width
        self.height = height

        super().__init__(
            vertices=self.generateVertices(),
            fillColor=TRANSPARENT,
            strokeColor=strokeColor,
            strokeWidth=strokeWidth,
            cornerRadius=cornerRadius,
        )

    def generateVertices(self) -> list[point]:
        if self.width is None or self.height is None:
            return []
        return [(0, 0), (self.width, 0), (self.width, self.height), (0, self.height)]

    @prop(onSet=Polygon.updatePoints)
    def width() -> maybe[wunumber]: ...

    @prop(onSet=Polygon.updatePoints)
    def height() -> maybe[wunumber]: ...

    def track(
        self,
        x: number,
        y: number,
        startFrame: frame = 0,
        endFrame: maybe[frame] = None,
    ) -> TrackedPath:
        """
        Track a point through this video's raw source frames using OpenCV's
        Lucas-Kanade sparse optical flow (`cv2.calcOpticalFlowPyrLK`),
        starting from pixel `(x, y)` — the source video's NATIVE pixel
        resolution, plain image coordinates (top-left origin, y-down), NOT
        world units — at `startFrame`, forward through to `endFrame`
        (exclusive; `None` tracks to the last decodable frame of the source).

        Returns a `TrackedPath`: `{sourceFrameIndex: (worldX, worldY)}`,
        already converted into this `Video`'s world-space coordinates (see
        the conversion math below). Pass it to `someInput.attachTo(path)` to
        make any other `Input` follow the tracked point frame-by-frame —
        e.g. `text.attachTo(video.track(x, y))`.

        Coordinate conversion: `(px, py) / (srcW, srcH)` is a 0..1 fraction
        across the source frame. `position()` places this `Video`'s bbox
        CENTER at `self.meta.position` under the default `align=(0.5, 0.5)`
        (verified via `getTransformationMatrixFromMetadata` in
        `IVertexShader.hpp`: with a centered pivot the position/pivot terms
        cancel to a pure translation of the bbox center to `(x, y)`). World Y
        is positive-upward while image Y is positive-downward (row 0 = top,
        matching `parsePointsJson`'s `-y` flip and the "local space Y is
        flipped relative to world space" convention documented in
        `BezierPath.cpp`); X is not flipped. So:

            worldX = centerX + width  * (px / srcW - 0.5)
            worldY = centerY + height * (0.5 - py / srcH)

        where `(centerX, centerY)` is `self.meta.position` and `width`/
        `height` are this `Video`'s world-unit shape size (explicit
        `width=`/`height=` if given, else the same natural-size fallback
        `__init__` uses for `cornerRadius`: native pixel size divided by
        `WORLD_TO_SCREEN_RATIO`).

        Requires `opencv-python` (`pip install opencv-python`) — imported
        lazily here, mirroring this project's lazy-import convention, so
        scripts that never call `.track()` don't need it installed at all;
        the C++ backend already links OpenCV, but there is no Python-side
        `cv2` dependency anywhere else in `videocode`.

        Tracking quality: LK optical flow degrades on fast motion, occlusion,
        featureless regions, or large lighting changes. When OpenCV reports
        lost tracking (`status == 0` for a frame), this holds the last
        known-good position for that and every following frame rather than
        raising or extrapolating — a static-but-not-silently-wrong result
        beats a crash. Inspect the returned `TrackedPath` if you suspect a
        lost track.

        Known V1 limitations:

        - Frame indices are in **source-frame space** — the same raw index
          space `cuts`/`startFrame`/`endFrame` cut against, NOT the post-cut/
          post-speedRamp playback timeline. If this `Video` also uses `cuts`
          or `speedRamps`, a tracked source-frame index doesn't automatically
          correspond to the same playback frame; realigning tracked
          positions to a retimed playback timeline is a possible future
          enhancement, not implemented here (mirrors the caveat already
          documented on `speedRamps` above).
        - The conversion assumes this `Video` is stationary: `self.meta.
          position` is read once, at call time, and baked into every
          returned position. If the `Video` itself moves during playback
          (`.position()`/`.moveTo()`/etc. applied to it over time), tracked
          positions won't follow — this is a one-shot snapshot of wherever
          the `Video` sits when `.track()` runs.
        - Seeking to `startFrame` uses OpenCV's `CAP_PROP_POS_FRAMES`, which
          is only as accurate as the container's keyframe index for some
          codecs. Reads from `startFrame` onward are sequential (no further
          seeking), which is the reliable part of the pipeline.
        """
        try:
            import cv2
            import numpy as np
        except ImportError as e:
            raise ImportError(
                "Video.track() needs OpenCV on the Python side — install it "
                "with `pip install opencv-python` (this is intentionally not "
                "a hard dependency of videocode: only .track() callers need it)."
            ) from e

        cap = cv2.VideoCapture(self.filepath)
        if not cap.isOpened():
            raise RuntimeError(f"Video.track(): OpenCV could not open '{self.filepath}'")

        try:
            srcW = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            srcH = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if srcW <= 0 or srcH <= 0:
                raise RuntimeError(f"Video.track(): OpenCV reported an invalid frame size for '{self.filepath}'")

            if endFrame is None:
                frameCount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                endFrame = frameCount if frameCount > startFrame else startFrame + 1

            width = self.width if self.width is not None else srcW / WORLD_TO_SCREEN_RATIO
            height = self.height if self.height is not None else srcH / WORLD_TO_SCREEN_RATIO

            # Snapshot — see the "assumes stationary" limitation above.
            centerX, centerY = self.meta.position.x, self.meta.position.y

            def toWorld(px: float, py: float) -> point:
                return _pixelToWorld(px, py, srcW, srcH, width, height, centerX, centerY)

            cap.set(cv2.CAP_PROP_POS_FRAMES, startFrame)
            ok, frameImg = cap.read()
            if not ok:
                raise RuntimeError(f"Video.track(): could not read startFrame={startFrame} from '{self.filepath}'")
            prevGray = cv2.cvtColor(frameImg, cv2.COLOR_BGR2GRAY)

            winSize = (21, 21)
            maxLevel = 3
            criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)

            pts = np.array([[[float(x), float(y)]]], dtype=np.float32)
            positions: dict[frame, point] = {startFrame: toWorld(x, y)}

            frameIdx = startFrame
            while frameIdx + 1 < endFrame:
                ok, frameImg = cap.read()
                if not ok:
                    break
                gray = cv2.cvtColor(frameImg, cv2.COLOR_BGR2GRAY)
                nextPts, status, _err = cv2.calcOpticalFlowPyrLK(
                    prevGray, gray, pts, np.empty_like(pts),
                    winSize=winSize, maxLevel=maxLevel, criteria=criteria,
                )
                frameIdx += 1
                if nextPts is not None and status is not None and status[0][0] == 1:
                    pts = nextPts
                # else: hold the last known-good pts (lost track — see docstring).
                px, py = float(pts[0][0][0]), float(pts[0][0][1])
                positions[frameIdx] = toWorld(px, py)
                prevGray = gray

            return TrackedPath(positions)
        finally:
            cap.release()
