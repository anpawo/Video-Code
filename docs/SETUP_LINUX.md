# Running Video-Code on Linux

This is a from-scratch setup guide for building and running the app on
Ubuntu/Debian-based Linux. The steps mirror the Linux job of
the `build` job of `.github/workflows/ci.yaml`, which is known to build green
— if something here stops working, that job is the reference to diff against.

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
    texlive-latex-base texlive-latex-extra \
    texlive-fonts-recommended dvisvgm \
    autoconf automake autoconf-archive libtool \
    flex bison \
    libgl1-mesa-dev libglu1-mesa-dev \
    libegl1-mesa-dev libgles2-mesa-dev \
    libx11-xcb-dev libxkbcommon-dev libxkbcommon-x11-dev libxi-dev libxtst-dev '^libxcb.*-dev'
```

- **autotools, flex, bison, and the X / GL / XCB headers** are not for the app:
  vcpkg builds its ports from source, and several of them reach for these on
  the system — gperf and libxcrypt want autotools, libpq (behind Qt's
  `sql-psql`) wants flex and bison, Qt's `xcb`, `opengl` and `egl` features and
  the at-spi2 stack behind OpenCV's GTK window want the X and GL headers.
  `'^libxcb.*-dev'` is an apt regex: every `libxcb-*-dev` at once, rather than
  the dozen names spelled out. GitHub's runners ship all of this preinstalled,
  which is why CI is green without naming any of it; a fresh machine is not.
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

> **Install into the interpreter the binary embeds, not into a venv.** The
> build links the base interpreter's `libpython`
> (`find_package(Python3 ... Development)`), and a venv has none of its own:
> at runtime the embedded interpreter imports from the base interpreter's
> `site-packages`, and a package that only exists in the venv is
> `ModuleNotFoundError` — the build passed, because `python3 -m pybind11`
> answered from the venv, and the first run fails on `PIL`.

That interpreter has to be **3.12 or newer** (the CMake lookup asks for it) and
has to be **the `python3` CMake sees at configure time**: first on `PATH`, or
named with `-DPython3_EXECUTABLE=…` in step 4 — and the one you `pip install`
into.

With pyenv, pick a 3.12+ version and stay in that shell for the build; pyenv's
interpreters are not externally managed, so `pip` works without a venv:

```bash
pyenv shell 3.13.3
python3 -m pip install pybind11 -r requirements.txt
# and stay in this shell for step 4
```

When the system `python3` is 3.12+ but refuses `pip` (PEP 668, "externally
managed"), pass `--break-system-packages` instead of making a venv — for the
same reason: the packages must land where the embedded interpreter looks.

CMake asks `python3 -m pybind11 --cmakedir` where pybind11's CMake config is,
so the `python3` it runs at configure time has to be the interpreter that
received the packages.

## 4. Build

```bash
cmake -S . -B build -G Ninja \
    -DCMAKE_C_COMPILER=gcc-13 \
    -DCMAKE_CXX_COMPILER=$(which g++-13) \
    -DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake \
    -DVCPKG_OVERLAY_TRIPLETS=$PWD/vcpkg-overlay-triplets \
    -DVCPKG_INSTALLED_DIR=$(pwd)/vcpkg_installed \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

cmake --build build
cp build/video-code .
```

- **`-DVCPKG_OVERLAY_TRIPLETS`** hands vcpkg the `x64-linux` triplet kept in
  this repository: the stock one plus a chainload toolchain
  (`cmake/vcpkg-toolchain-gcc13.cmake`) that builds the *dependencies* with
  GCC 13 as well, not only the app. Left to the system compiler, a distro on
  GCC 15 stops on several of the older ports. The chainload re-includes vcpkg's
  own `linux.cmake`, so `-fPIC` and the architecture detection are unchanged.
- **`-DCMAKE_C_COMPILER=gcc-13`** keeps the C objects on the same toolchain as
  the C++ ones.
- *"another vcpkg may be running"*, or permission errors under
  `vcpkg_installed/`: a build was once run with `sudo` and left root-owned
  files behind. `sudo chown -R "$USER:$USER" vcpkg_installed`, and never `sudo`
  the build.
- Short on disk:
  `-DVCPKG_INSTALL_OPTIONS="--clean-buildtrees-after-build;--clean-packages-after-build"`
  makes vcpkg drop each port's intermediates as it finishes them; a cold build
  otherwise leaves 15 GB and more under `~/vcpkg/buildtrees`.

Which version of each dependency gets built is fixed by the baseline commit in
`vcpkg-configuration.json` — a 2026 vcpkg commit, chosen so the whole set
compiles on today's toolchains (GCC 15, glibc 2.43).

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
