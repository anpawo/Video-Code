# Running Video-Code on Linux

This is a from-scratch setup guide for building and running the app on
Ubuntu/Debian-based Linux. The steps mirror the Linux job of
`.github/workflows/ci-build.yaml`, which is known to build green — if
something here stops working, that workflow is the reference to diff
against.

Steps 1-3 (system packages, vcpkg, Python deps) are automated by
[`scripts/setup-linux.sh`](../scripts/setup-linux.sh) — run it, then jump to
[4. Build](#4-build).

## 1. System dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential cmake ninja-build python3-dev \
    ffmpeg libopencv-dev libcurl4-openssl-dev \
    libvulkan-dev libfreetype6-dev \
    glslang-dev glslang-tools \
    g++-13 gcc-13 \
    mesa-vulkan-drivers \
    texlive-latex-base texlive-latex-extra texlive-fonts-recommended dvisvgm
```

- **g++-13 / gcc-13**: the project requires C++20 and `CMakeLists.txt` hard-fails
  if `CMAKE_CXX_COMPILER_VERSION` isn't > 13. Point CMake at it explicitly
  (step 4) rather than relying on the system default `g++`.
- **mesa-vulkan-drivers**: provides a software/Mesa Vulkan ICD. If you have a
  real GPU with vendor Vulkan drivers (NVIDIA/AMD/Intel), that's fine too —
  just make sure `vulkaninfo` (from `vulkan-tools`) lists at least one device.
- **texlive-\* / dvisvgm**: needed by `MathTex`/`Tex`
  (`videocode/input/shape/tex/`), which compiles LaTeX to SVG via `latex` +
  `dvisvgm --no-fonts`. Ghostscript is *not* required — it's only needed for
  PostScript specials (e.g. `tikz`), which `amsmath`/`amssymb` don't use.
- The Qt preview window needs an X11 (or XWayland) display. If you're on a
  headless box/VM, you'll still be able to use `--generate` and
  `--visual-test` (both run headless via the Vulkan headless renderer), but
  not the live preview window.

## 2. vcpkg

The C++ dependencies (Qt6, OpenCV, FFmpeg, Vulkan headers, FreeType, etc. —
see `vcpkg.json`) are managed by vcpkg, not apt.

```bash
git clone https://github.com/microsoft/vcpkg.git ~/vcpkg
~/vcpkg/bootstrap-vcpkg.sh
echo 'export VCPKG_ROOT=$HOME/vcpkg' >> ~/.bashrc
export VCPKG_ROOT=$HOME/vcpkg
```

`CMakeLists.txt` fails fast with `VCPKG_ROOT environment variable not set` if
this isn't exported.

**First build will be slow.** vcpkg builds `qtbase` (with the `xcb` feature
on Linux), OpenCV, FFmpeg, protobuf, etc. from source — this can take well
over an hour on a cold cache. Subsequent builds reuse `vcpkg_installed/`.

## 3. Python dependencies

The C++ binary embeds a Python interpreter (pybind11) to run user scripts —
both the C++ build and the runtime need the same Python 3 (>= 3.12) with
these packages:

```bash
pip install pybind11 -r requirements.txt
```

`requirements.txt` currently includes: `shapely`, `freetype-py`, `uharfbuzz`,
`Pillow`, `svgelements`, `typing_extensions`.

If `pip install` is externally-managed-environment-blocked on your distro,
use a venv:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pybind11 -r requirements.txt
```

(CMake calls `python3 -m pybind11 --cmakedir` to locate pybind11's CMake
config — make sure that `python3` is the same interpreter/env you installed
into.)

## 4. Build

```bash
cmake -S . -B build -G Ninja \
    -DCMAKE_CXX_COMPILER=$(which g++-13) \
    -DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake \
    -DVCPKG_INSTALLED_DIR=$(pwd)/vcpkg_installed \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

cmake --build build
cp build/video-code .
```

This matches what CI does. `make cmake` (the Makefile target) runs the same
configure+build but its final `cp` step
(`build/$(BINARY_NAME).app/Contents/MacOS/$(BINARY_NAME)`) assumes the macOS
`.app` bundle layout (`MACOSX_BUNDLE TRUE` is Apple-only in `CMakeLists.txt`).
On Linux the binary is just `build/video-code` — that `cp` will fail and
`make` will stop with an error *after* the build already succeeded. Either:
- use the direct `cmake`/`cp` commands above, or
- run `make cmake`, ignore the trailing cp error, and `cp build/video-code .`
  yourself.

`make debug` (adds `-g3 -O0 -DVC_DEBUG_ON`) and `make verbose` (adds
`-DVC_VERBOSE`, prints `[startup]` phase-timing) have the same caveat.

## 5. Run

```bash
./video-code                       # live preview window (Qt), edits video.py
./video-code --file myscene.py     # preview a specific script
./video-code --generate out.mp4    # headless render to mp4
./video-code --generate out.png    # headless render a single frame to an image
./video-code --visual-test         # run the visual-regression suite
```

Scenes are plain Python files using the `videocode` API (see `video.py` for
a living example, and `docs/FEATURES.md` for a feature-by-feature tour).

### Preview window controls

Press `H` in the preview window to toggle an in-app cheat sheet. Summary:

| Key | Action |
|---|---|
| `Escape` | Close window / dismiss help overlay |
| `Space` | Pause / resume |
| `Left` / `Right` | Step ±1 frame (±5 with Ctrl) |
| `Down` / `Up` | Go to first / last frame |
| `Ctrl+Down` / `Ctrl+Up` | Go to previous / next timestamp |
| `Ctrl+R` | Reload the source file (hot-reload, only changed inputs rebuild) |
| `Ctrl+S` | Export the current frame to an image |
| `H` | Toggle help overlay |

## 6. Troubleshooting

- **`VCPKG_ROOT environment variable not set`** — re-export it (step 2),
  or add it to your shell profile.
- **`C++20 requires GCC 13 or higher`** — make sure
  `-DCMAKE_CXX_COMPILER=$(which g++-13)` was passed; delete `build/` and
  reconfigure if you built once with the wrong compiler (CMake caches it).
- **Vulkan init fails / no devices** — run `vulkaninfo` to check a driver is
  visible. On a VM/CI box, `mesa-vulkan-drivers` (lavapipe, software) is
  enough for headless `--generate`/`--visual-test`; the live preview window
  additionally needs a display.
- **Qt window doesn't appear over SSH** — you need an X11 display (`ssh -X`)
  or a local X/Wayland session; headless boxes can still use `--generate`.
- **`pybind11_DIR` / pybind11 not found** — `python3 -m pybind11 --cmakedir`
  must succeed; make sure `pip install pybind11` was run for the same
  `python3` CMake resolves to.
