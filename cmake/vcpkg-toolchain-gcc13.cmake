# Chainload toolchain used by the overlay triplet so vcpkg builds every
# dependency with GCC 13 instead of the system default (GCC 15), which fails
# to compile ports like libxcrypt under -Werror.
#
# VCPKG_CHAINLOAD_TOOLCHAIN_FILE *replaces* vcpkg's stock toolchain, so we must
# re-inherit it — otherwise we lose -fPIC (breaks static libs linked into .so
# modules like libffi -> libatk-bridge.so), the correct CMAKE_SYSTEM_PROCESSOR,
# and CMAKE_CROSSCOMPILING OFF. We set the compiler first; linux.cmake only
# assigns a compiler inside its cross-compile branch (skipped on a native
# x86_64 build), so our choice survives.
set(CMAKE_C_COMPILER /usr/bin/gcc-13)
set(CMAKE_CXX_COMPILER /usr/bin/g++-13)

if(NOT DEFINED _VCPKG_ROOT_DIR)
    set(_VCPKG_ROOT_DIR "$ENV{VCPKG_ROOT}")
endif()
include("${_VCPKG_ROOT_DIR}/scripts/toolchains/linux.cmake")
