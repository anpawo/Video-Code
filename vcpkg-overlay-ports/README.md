# Overlay ports

Local copies of upstream vcpkg ports, used only where upstream cannot build on
this project's machines. Wired in through `-DVCPKG_OVERLAY_PORTS` (see the
`Makefile`), so they apply to every configure without anyone remembering a flag.

## The Qt submodules — `qtdeclarative`, `qtlanguageserver`, `qtshadertools`, `qtsvg`

Pulled in by the editor chrome, which is QML (`Qt6::Quick`). On macOS they refuse
to configure without a **full Xcode install**: Qt's own
`_qt_internal_check_apple_sdk_and_xcode_versions` runs `xcodebuild`, which the
Command Line Tools do not ship, and stops with

    Can't determine Xcode version. Is Xcode installed?

Nothing in the build actually needs Xcode — the SDK bundled with the Command Line
Tools is what compiles everything, and `qtbase` itself builds fine. Only the
*version check* fails. Each overlay portfile therefore prepends, under `if(APPLE)`:

    list(APPEND VCPKG_CMAKE_CONFIGURE_OPTIONS "-DQT_NO_XCODE_MIN_VERSION_CHECK:BOOL=ON")

`vcpkg_cmake_configure` reads that variable from its calling scope, so setting it
in the portfile is enough — no patch, no fork of the build logic.

### Why not the triplet

`VCPKG_CMAKE_CONFIGURE_OPTIONS` also works from a triplet file, and there is
already an overlay triplet for Linux. But triplet contents feed every port's ABI
hash, so adding one line there would rebuild opencv, ffmpeg, protobuf, curl,
glslang and freetype from source. Scoping it to the four ports that need it costs
nothing: they had never been built.

### Cost, and how to get rid of it

These copies are **pinned at 6.11.1** and do not follow the vcpkg baseline. Bumping
Qt means re-copying them from the registry and re-applying the block above.

The clean fix is to install Xcode and `xcode-select -s` it, then delete these four
directories and the `-DVCPKG_OVERLAY_PORTS` flag from the `Makefile`. Worth doing
on a machine that also debugs a Vulkan-through-MoltenVK renderer, since that is
where the Metal frame-capture tooling lives.
