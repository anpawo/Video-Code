#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <plugin-name> <plugin-source-dir> <output-dir>"
  exit 1
fi

PLUGIN_NAME="$1"
PLUGIN_SOURCE_DIR="$2"
OUTPUT_DIR="$3"

CPP_SOURCE_DIR="${PLUGIN_SOURCE_DIR}/cpp"
PY_SOURCE_DIR="${PLUGIN_SOURCE_DIR}/python"
PLUGIN_OUTPUT_DIR="${OUTPUT_DIR}/${PLUGIN_NAME}"
CPP_BUILD_DIR="${PLUGIN_OUTPUT_DIR}/cpp-build"
CPP_OUTPUT_DIR="${PLUGIN_OUTPUT_DIR}/cpp"
PY_OUTPUT_DIR="${PLUGIN_OUTPUT_DIR}/python"
METADATA_PATH="${PLUGIN_OUTPUT_DIR}/${PLUGIN_NAME}.json"

if [[ ! -d "$CPP_SOURCE_DIR" ]]; then
  echo "Missing C++ source directory: $CPP_SOURCE_DIR"
  exit 2
fi

if [[ ! -d "$PY_SOURCE_DIR" ]]; then
  echo "Missing Python source directory: $PY_SOURCE_DIR"
  exit 3
fi

mkdir -p "$CPP_BUILD_DIR" "$CPP_OUTPUT_DIR" "$PY_OUTPUT_DIR"

VCPKG_ARGS=()
if [[ -n "${VCPKG_ROOT:-}" ]]; then
  VCPKG_ARGS+=("-DCMAKE_TOOLCHAIN_FILE=${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake")
  VCPKG_ARGS+=("-DVCPKG_INSTALLED_DIR=$PWD/vcpkg_installed")

  TRIPLET="${VCPKG_TARGET_TRIPLET:-x64-linux}"
  NLOHMANN_INCLUDE="$PWD/vcpkg_installed/$TRIPLET/include"
  if [[ -d "$NLOHMANN_INCLUDE" ]]; then
    VCPKG_ARGS+=("-DCMAKE_CXX_FLAGS=-I$NLOHMANN_INCLUDE")
  fi
fi

cmake -S "$CPP_SOURCE_DIR" -B "$CPP_BUILD_DIR" -DVIDEO_CODE_ROOT="$PWD" "${VCPKG_ARGS[@]}"
cmake --build "$CPP_BUILD_DIR"

CPP_LIBRARY="$(find "$CPP_BUILD_DIR" -maxdepth 1 -type f \( -name '*.so' -o -name '*.dylib' \) | head -n1)"
if [[ -z "$CPP_LIBRARY" ]]; then
  echo "Could not locate built C++ plugin shared library in $CPP_BUILD_DIR"
  exit 4
fi

CPP_LIBRARY_NAME="$(basename "$CPP_LIBRARY")"
cp -f "$CPP_LIBRARY" "$CPP_OUTPUT_DIR/$CPP_LIBRARY_NAME"

PY_MODULE="$(find "$PY_SOURCE_DIR" -maxdepth 1 -type f -name '*.py' | head -n1)"
if [[ -z "$PY_MODULE" ]]; then
  echo "Could not locate python plugin module in $PY_SOURCE_DIR"
  exit 5
fi

PY_MODULE_NAME="$(basename "$PY_MODULE")"
cp -f "$PY_MODULE" "$PY_OUTPUT_DIR/$PY_MODULE_NAME"
python3 -m compileall "$PY_OUTPUT_DIR" >/dev/null

cat > "$METADATA_PATH" <<JSON
{
  "name": "$PLUGIN_NAME",
  "cpp_library": "cpp/$CPP_LIBRARY_NAME",
  "python_module": "python/$PY_MODULE_NAME"
}
JSON

echo "Built plugin '$PLUGIN_NAME' in $PLUGIN_OUTPUT_DIR"
