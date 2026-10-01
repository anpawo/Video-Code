#!/bin/bash
#
# Installs the dependencies needed to build Video-Code on Linux, following
# docs/SETUP_LINUX.md. Targets Ubuntu/Debian (apt-based) distros.
#
# Usage:
#   ./scripts/setup-linux.sh
#
# After this completes, see docs/SETUP_LINUX.md "4. Build" for the
# cmake/build commands.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VCPKG_DIR="${VCPKG_ROOT:-$HOME/vcpkg}"

if ! command -v apt-get >/dev/null 2>&1; then
    echo "error: this script requires apt-get (Ubuntu/Debian)." >&2
    exit 1
fi

echo "==> Installing system dependencies (apt)"
sudo apt-get update
packages=(
    # the toolchain, and what the app itself links
    build-essential cmake ninja-build g++-13 gcc-13 git curl
    python3-dev python3-pip
    ffmpeg libopencv-dev libcurl4-openssl-dev libvulkan-dev libfreetype6-dev
    glslang-dev glslang-tools mesa-vulkan-drivers
    # MathTex / Tex
    texlive-latex-base texlive-latex-extra texlive-fonts-recommended dvisvgm
    # what vcpkg's ports expect to find on the system while they build: autotools
    # for gperf and libxcrypt, flex and bison for libpq, the X and GL headers for
    # Qt's xcb/opengl/egl features and for the at-spi2 stack behind OpenCV's GTK
    # window. GitHub's runners have every one of these preinstalled; a fresh
    # machine has none. The regex is apt's: every libxcb-*-dev in one word.
    autoconf automake autoconf-archive libtool flex bison
    libgl1-mesa-dev libglu1-mesa-dev libegl1-mesa-dev libgles2-mesa-dev
    libx11-xcb-dev libxkbcommon-dev libxkbcommon-x11-dev libxi-dev libxtst-dev '^libxcb.*-dev'
)
sudo apt-get install -y "${packages[@]}"

echo "==> Setting up vcpkg"
if [ -d "$VCPKG_DIR" ]; then
    echo "    $VCPKG_DIR already exists, skipping clone."
else
    git clone https://github.com/microsoft/vcpkg.git "$VCPKG_DIR"
fi

if [ ! -x "$VCPKG_DIR/vcpkg" ]; then
    "$VCPKG_DIR/bootstrap-vcpkg.sh"
fi

for rcfile in "$HOME/.bashrc" "$HOME/.zshrc"; do
    [ -f "$rcfile" ] || continue
    if ! grep -q "^export VCPKG_ROOT=" "$rcfile" 2>/dev/null; then
        echo "export VCPKG_ROOT=$VCPKG_DIR" >> "$rcfile"
        echo "    Added 'export VCPKG_ROOT=$VCPKG_DIR' to $rcfile"
    fi
done
export VCPKG_ROOT="$VCPKG_DIR"

echo "==> Installing Python dependencies"
if ! pip install pybind11 -r "$REPO_ROOT/requirements.txt"; then
    echo "    pip install failed (likely PEP 668 externally-managed-environment) — retrying with --break-system-packages"
    pip install --break-system-packages pybind11 -r "$REPO_ROOT/requirements.txt"
fi

cat <<EOF

==> Done.

VCPKG_ROOT=$VCPKG_DIR (added to your shell rc — open a new shell, or run
'export VCPKG_ROOT=$VCPKG_DIR' in this one, before building).

Next: build the project — see docs/SETUP_LINUX.md, section "4. Build":

  cmake -S . -B build -G Ninja \\
      -DCMAKE_C_COMPILER=gcc-13 \\
      -DCMAKE_CXX_COMPILER=\$(which g++-13) \\
      -DCMAKE_TOOLCHAIN_FILE=\$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake \\
      -DVCPKG_OVERLAY_TRIPLETS=\$PWD/vcpkg-overlay-triplets \\
      -DVCPKG_INSTALLED_DIR=\$(pwd)/vcpkg_installed \\
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

  cmake --build build

The first build will be slow (vcpkg builds Qt6/OpenCV/FFmpeg from source).
EOF
