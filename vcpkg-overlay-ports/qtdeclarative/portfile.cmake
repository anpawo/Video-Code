# ── Local overlay ─────────────────────────────────────────────────────────────
# Qt submodules refuse to configure without a full Xcode install: the version
# check in QtPublicAppleHelpers.cmake calls xcodebuild, which Command Line Tools
# alone do not provide, and errors out with "Can't determine Xcode version".
# Nothing in the build needs Xcode itself — the SDK the CLT ship with is enough —
# so the check is skipped. vcpkg_cmake_configure reads this variable from the
# calling scope, which is why setting it here is enough.
#
# Delete this whole overlay once Xcode is installed: it pins these ports at
# 6.11.1 and will not follow the vcpkg baseline on its own.
if(APPLE)
    list(APPEND VCPKG_CMAKE_CONFIGURE_OPTIONS "-DQT_NO_XCODE_MIN_VERSION_CHECK:BOOL=ON")
endif()

set(SCRIPT_PATH "${CURRENT_INSTALLED_DIR}/share/qtbase")
include("${SCRIPT_PATH}/qt_install_submodule.cmake")

vcpkg_buildpath_length_warning(44)

set(${PORT}_PATCHES "")

 set(TOOL_NAMES
        qml
        qmlaotstats
        qmlcachegen
        qmlcontextpropertydump
        qmleasing
        qmlformat
        qmlimportscanner
        qmllint
        qmlplugindump
        qmlpreview
        qmlprofiler
        qmlscene
        qmltestrunner
        qmltime
        qmltyperegistrar
        qmldom
        qmltc
        qmlls
        qmljsrootgen
        svgtoqml
    )

qt_install_submodule(PATCHES    ${${PORT}_PATCHES}
                     TOOL_NAMES ${TOOL_NAMES}
                     CONFIGURE_OPTIONS
                      -DCMAKE_DISABLE_FIND_PACKAGE_LTTngUST:BOOL=ON
                     CONFIGURE_OPTIONS_RELEASE
                     CONFIGURE_OPTIONS_DEBUG
                    )
