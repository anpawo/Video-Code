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
sudo apt-get install -y \
    build-essential cmake ninja-build python3-dev python3-pip \
    ffmpeg libopencv-dev libcurl4-openssl-dev \
    libvulkan-dev libfreetype6-dev \
    glslang-dev glslang-tools \
    g++-13 gcc-13 \
    mesa-vulkan-drivers \
    texlive-latex-base texlive-latex-extra texlive-fonts-recommended dvisvgm \
    git curl

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
      -DCMAKE_CXX_COMPILER=\$(which g++-13) \\
      -DCMAKE_TOOLCHAIN_FILE=\$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake \\
      -DVCPKG_INSTALLED_DIR=\$(pwd)/vcpkg_installed \\
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

  cmake --build build
  cp build/video-code .

The first build will be slow (vcpkg builds Qt6/OpenCV/FFmpeg from source).
EOF
