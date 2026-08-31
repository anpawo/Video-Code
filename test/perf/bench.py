#!/usr/bin/env python3

"""
Performance benchmark for video-code — measures the metrics tracked in
docs/optimization.md.

Usage (from the repo root, after `make cmake`):

    python3 test/perf/bench.py

Measures, over 3 runs of rendering test/perf/stress_text.py (best run kept):
  - load time      (process start -> first frame written)
  - render speed   (ms per frame once rendering starts)
  - total wall time
  - peak RSS       (maximum resident set size of the renderer)
plus the wall time of the full visual-test suite.
"""

import re
import subprocess
import sys
import time

SCENE = "test/perf/stress_text.py"
OUT = "/tmp/vc_bench_out.mp4"
RUNS = 3


def renderOnce() -> dict:
    t0 = time.perf_counter()
    proc = subprocess.Popen(
        ["/usr/bin/time", "-l", "./video-code", "--file", SCENE, "--generate", OUT],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
    )
    firstFrame = None
    buf = b""
    while True:
        chunk = proc.stdout.read(256)
        if not chunk:
            break
        buf += chunk
        # progress reads "1/300 frames" — the renderer prints the count AFTER the ratio
        if firstFrame is None and re.search(rb"\b1/\d+ frames", buf):
            firstFrame = time.perf_counter() - t0
    proc.wait()
    total = time.perf_counter() - t0

    text = buf.decode(errors="replace")
    # A render that died — the machine ran out of memory, ffmpeg was missing,
    # the scene raised — leaves no progress line, and `.group(1)` on None threw
    # an AttributeError that looked exactly like a bug in the benchmark. Say
    # what actually happened instead, with the child's own words.
    def read(pattern: str, what: str) -> int:
        hit = re.search(pattern, text)
        if hit is None:
            raise SystemExit(f"the render did not report {what} — it exited {proc.returncode}:\n{text[-1500:]}")
        return int(hit.group(1))

    frames = read(r"\d+/(\d+) frames", "how many frames it rendered")
    rss = read(r"(\d+)\s+maximum resident set size", "its peak memory")

    if firstFrame is None:
        raise SystemExit(f"the render never reached its first frame — it exited {proc.returncode}:\n{text[-1500:]}")

    return {
        "load": firstFrame,
        "total": total,
        "msPerFrame": (total - firstFrame) / frames * 1000,
        "frames": frames,
        "rssMb": rss / (1024 * 1024),
    }


def main() -> int:
    runs = [renderOnce() for _ in range(RUNS)]
    best = min(runs, key=lambda r: r["total"])

    t0 = time.perf_counter()
    suite = subprocess.run(["./video-code", "--visual-test"], capture_output=True)
    suiteSecs = time.perf_counter() - t0
    suiteOk = suite.returncode == 0

    print(f"scene: {SCENE} ({best['frames']} frames), best of {RUNS} runs")
    print(f"load (start -> first frame): {best['load']:.2f} s")
    print(f"render:                      {best['msPerFrame']:.1f} ms/frame")
    print(f"total:                       {best['total']:.2f} s")
    print(f"peak RSS:                    {best['rssMb']:.0f} MB")
    print(f"visual-test suite:           {suiteSecs:.2f} s ({'PASS' if suiteOk else 'FAIL'})")
    print()
    print(f"| {best['load']:.2f} s | {best['msPerFrame']:.1f} ms | {best['total']:.2f} s "
          f"| {best['rssMb']:.0f} MB | {suiteSecs:.1f} s |")
    return 0 if suiteOk else 1


if __name__ == "__main__":
    sys.exit(main())
