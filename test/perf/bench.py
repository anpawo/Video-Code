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
        if firstFrame is None and b"frame 1/" in buf:
            firstFrame = time.perf_counter() - t0
    proc.wait()
    total = time.perf_counter() - t0

    text = buf.decode(errors="replace")
    frames = int(re.search(r"frame \d+/(\d+)", text).group(1))
    rss = int(re.search(r"(\d+)\s+maximum resident set size", text).group(1))

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
