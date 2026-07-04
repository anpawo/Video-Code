# Overlay triplet: same as vcpkg's built-in x64-linux, but chainloads a
# toolchain pinning GCC 13. Keeps the triplet name "x64-linux" so nothing
# else (manifest, installed-dir layout) needs to change.
set(VCPKG_TARGET_ARCHITECTURE x64)
set(VCPKG_CRT_LINKAGE dynamic)
set(VCPKG_LIBRARY_LINKAGE static)

set(VCPKG_CMAKE_SYSTEM_NAME Linux)

set(VCPKG_CHAINLOAD_TOOLCHAIN_FILE "${CMAKE_CURRENT_LIST_DIR}/../cmake/vcpkg-toolchain-gcc13.cmake")
