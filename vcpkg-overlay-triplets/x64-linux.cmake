# vcpkg's own x64-linux, plus the chainload toolchain that pins GCC 13 for the
# ports. Same name on purpose: the manifest and the vcpkg_installed/ layout do
# not notice the difference.
set(VCPKG_TARGET_ARCHITECTURE x64)
set(VCPKG_CRT_LINKAGE dynamic)
set(VCPKG_LIBRARY_LINKAGE static)
set(VCPKG_CMAKE_SYSTEM_NAME Linux)
set(VCPKG_CHAINLOAD_TOOLCHAIN_FILE "${CMAKE_CURRENT_LIST_DIR}/../cmake/vcpkg-toolchain-gcc13.cmake")
