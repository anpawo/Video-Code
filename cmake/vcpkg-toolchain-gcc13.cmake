# Handed to vcpkg by vcpkg-overlay-triplets/x64-linux.cmake, so that every port
# is built with GCC 13 rather than the distro's default: a GCC 15 stops on
# -Werror in several of the older ports, libxcrypt among them.
#
# A chainload toolchain stands in for vcpkg's own, it is not layered on top of
# it. Without the include at the end there is no -fPIC (and a static libffi then
# refuses to go into libatk-bridge.so), no CMAKE_SYSTEM_PROCESSOR, and
# CMAKE_CROSSCOMPILING is left unset. The compiler is named first: linux.cmake
# only picks one on its cross-compiling path, which a native x86_64 build never
# takes, so the choice made here stands.
set(CMAKE_C_COMPILER /usr/bin/gcc-13)
set(CMAKE_CXX_COMPILER /usr/bin/g++-13)

if(NOT _VCPKG_ROOT_DIR)
    set(_VCPKG_ROOT_DIR "$ENV{VCPKG_ROOT}")
endif()
include("${_VCPKG_ROOT_DIR}/scripts/toolchains/linux.cmake")
