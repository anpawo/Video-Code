cmake_minimum_required(VERSION 3.21)
project(video-code VERSION 1.0.0 LANGUAGES CXX)

# OBJCXX (Objective-C++, for src/vulkan/MetalSurface.mm) is only needed on
# Apple. Probing for it on the project() call breaks Linux CI: g++-13 has no
# cc1objplus, so the OBJCXX compiler check fails before configure can proceed.
if(APPLE)
    enable_language(OBJCXX)
endif()

# Generate compile_commands.json automatically
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wno-deprecated -Wno-missing-field-initializers -pipe -D_REENTRANT -DQT_NO_DEBUG -DQT_WIDGETS_LIB -DQT_GUI_LIB -DQT_CORE_LIB -DQT_NO_KEYWORDS")

if(DEBUG)
    message(STATUS ">>> Debug build <<<")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g3 -O0 -DVC_DEBUG_ON")
else()
    message(STATUS ">>> Release build <<<")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2")
endif()

# `make verbose` — release build + the VC_SLOG/[startup] phase-timing prints.
if(VC_VERBOSE)
    message(STATUS ">>> VC_VERBOSE startup diagnostics enabled <<<")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DVC_VERBOSE")
endif()

set_property(GLOBAL PROPERTY CXX_STANDARD 20)

if(NOT CMAKE_CXX_COMPILER_VERSION VERSION_GREATER 13)
    message(FATAL_ERROR "C++20 requires GCC 13 or higher")
endif()

if(NOT DEFINED ENV{VCPKG_ROOT})
    message(FATAL_ERROR "VCPKG_ROOT environment variable not set")
endif()

set(VCPKG_ROOT $ENV{VCPKG_ROOT})
set(CMAKE_TOOLCHAIN_FILE "${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake" CACHE STRING "Vcpkg toolchain file")
set(VCPKG_FEATURE_FLAGS "manifests")
set(VCPKG_MANIFEST_MODE ON)

set(OPENCV_LOG_LEVEL "ERROR")
set(WITH_FFMPEG "ON")

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

if(NOT DEFINED VCPKG_TARGET_TRIPLET)
    if(WIN32)
        message(STATUS ">>> Windows build <<<")
        set(VCPKG_TARGET_TRIPLET "x64-windows")
    elseif(UNIX AND NOT APPLE)
        message(STATUS ">>> Linux build <<<")
        set(VCPKG_TARGET_TRIPLET "x64-linux")
    elseif(APPLE)
        message(STATUS ">>> Apple build <<<")
        set(VCPKG_TARGET_TRIPLET "x64-osx")
    endif()
endif()

set(CMAKE_PREFIX_PATH "${CMAKE_PREFIX_PATH};${CMAKE_SOURCE_DIR}/vcpkg_installed/${VCPKG_TARGET_TRIPLET}")

if(CI_BUILD)
    message(STATUS "CI_BUILD is defined")
    include(FetchContent)
    FetchContent_Declare(
        argparse
        GIT_REPOSITORY https://github.com/p-ranav/argparse.git
    )
    FetchContent_MakeAvailable(argparse)

    FetchContent_Declare(
        nlohmann_json
        GIT_REPOSITORY https://github.com/nlohmann/json.git
    )
    FetchContent_MakeAvailable(nlohmann_json)

    # earcut-hpp is header-only with no usable CMake target — just populate the
    # source and add its include dir directly.
    FetchContent_Declare(
        earcut
        GIT_REPOSITORY https://github.com/mapbox/earcut.hpp.git
        GIT_TAG v2.2.4
    )
    FetchContent_Populate(earcut)
    include_directories(${earcut_SOURCE_DIR}/include)
endif()

find_package(OpenCV CONFIG REQUIRED)
find_package(Python3 3.12 REQUIRED COMPONENTS Development Development.Module Development.Embed)
# pybind11 is pip-installed, not in any system CMake registry.
# Ask it directly where its CMake config lives, then point find_package at that path.
# (pybind11_DIR is the conventional hint variable find_package uses for pybind11Config.cmake)
execute_process(
    COMMAND python3 -m pybind11 --cmakedir
    OUTPUT_VARIABLE pybind11_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE  # strip the trailing newline or the path is invalid
)
find_package(pybind11 REQUIRED)
# Quick/Qml carry the editor chrome, which is described in .qml loaded at
# runtime — a layout change costs a reload, not a rebuild. See docs/ui/BACKLOG.md.
find_package(Qt6 REQUIRED COMPONENTS Widgets Core Gui Quick Qml QuickControls2)
# GuiPrivate: the scripted-run probe hands Qt the window activation the platform
# refuses to a binary launched from a terminal (src/window/Editor.cpp). OPTIONAL,
# and the one call behind it is compiled out when it is absent — the prebuilt Qt
# that CI installs ships no private headers, and a build that never opens a
# window has no use for them. Said at configure time rather than skipped, so a
# developer who loses the probe learns it here and not by wondering why VC_CLICK
# stopped working.
find_package(Qt6 QUIET COMPONENTS GuiPrivate)
if(Qt6GuiPrivate_FOUND)
    add_compile_definitions(VC_HAS_QPA_FOCUS)
else()
    message(STATUS "Qt6 GuiPrivate not found — the scripted-run focus probe is compiled out; VC_CLICK runs will not receive keyboard shortcuts.")
endif()

find_package(CURL REQUIRED)
if(APPLE)
    execute_process(COMMAND brew --prefix molten-vk OUTPUT_VARIABLE MVK_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE)
    set(Vulkan_LIBRARY "${MVK_PREFIX}/lib/libMoltenVK.dylib")
    set(Vulkan_INCLUDE_DIR "${MVK_PREFIX}/libexec/include")
endif()
find_package(Vulkan REQUIRED)
if(APPLE)
    # Talk to MoltenVK DIRECTLY, never through the loader.
    #
    # Enabling qtbase's `vulkan` feature dragged vcpkg's vulkan-loader into the
    # install tree, and FindVulkan then prefers it over the Vulkan_LIBRARY set
    # above — which is not a cosmetic difference: this machine has no ICD manifest
    # anywhere, so the loader finds no driver and vkCreateInstance fails for every
    # headless render. Forcing the imported target's location keeps our own Vulkan
    # calls bound to MoltenVK, the way they were before Quick needed Qt's Vulkan
    # support. Qt is unaffected: Qt6::Gui asks only for WrapVulkanHeaders and
    # resolves the library itself at runtime.
    set_target_properties(Vulkan::Vulkan PROPERTIES
        IMPORTED_LOCATION "${MVK_PREFIX}/lib/libMoltenVK.dylib"
    )
endif()
find_package(glslang CONFIG REQUIRED)
find_package(Freetype REQUIRED)

if(NOT CI_BUILD)
    find_package(nlohmann_json CONFIG REQUIRED)
    set(argparse_DIR "${VCPKG_ROOT}/installed/${VCPKG_TARGET_TRIPLET}/share/argparse")
    find_package(argparse CONFIG REQUIRED)
endif()

include_directories(
    ${OpenCV_INCLUDE_DIRS}
    ${CMAKE_SOURCE_DIR}/include
    ${Python3_INCLUDE_DIRS}
    ${FFMPEG_INCLUDE_DIRS}
    ${Vulkan_INCLUDE_DIRS}
)

set(SOURCES
    # --- Main ---
    src/Main.cpp

    # --- Window ---
    include/window/Window.hpp         # MOC Q_OBJECT
    include/window/TimelineWidget.hpp # MOC Q_OBJECT
    include/window/VulkanWidget.hpp   # MOC Q_OBJECT
    include/window/Editor.hpp         # MOC Q_OBJECT
    include/window/PreviewItem.hpp    # MOC Q_OBJECT
    include/window/PythonHighlighter.hpp # MOC Q_OBJECT
    include/window/ThumbProvider.hpp

    # --- Language server ---
    include/lsp/LanguageServer.hpp    # MOC Q_OBJECT
    include/agent/AgentSession.hpp    # MOC Q_OBJECT
    src/window/Window.cpp
    src/window/VulkanWidget.cpp
    src/window/Editor.cpp
    src/window/PreviewItem.cpp
    src/window/PythonHighlighter.cpp
    src/window/ThumbProvider.cpp
    src/lsp/LanguageServer.cpp
    src/agent/AgentSession.cpp

    # --- Vulkan ---
    src/vulkan/ShaderCompiler.cpp
    src/vulkan/VulkanHeadlessRenderer.cpp

    # --- Compiler ---
    src/compiler/Compiler.cpp

    # --- Test ---
    src/test/VisualTest.cpp

    # --- Core ---
    src/core/Core.cpp
    src/core/ScreenSize.cpp

    # --- Inputs ---
    src/input/AInput.cpp
    src/input/shape/BezierPath.cpp
    src/input/shape/Polygon.cpp
    src/input/media/Image.cpp
    src/input/media/Video.cpp
    src/input/media/Sound.cpp

    # --- Fragment Shaders (GLSL-based, no C++ impl needed) ---
)

if(APPLE)
    list(APPEND SOURCES src/vulkan/MetalSurface.mm)
    # The application menu's title, which only Cocoa can be told.
    list(APPEND SOURCES src/window/MacApplication.mm)
else()
    list(APPEND SOURCES src/vulkan/MetalSurfaceStub.cpp)
    list(APPEND SOURCES src/window/MacApplicationStub.cpp)
endif()

add_executable(${PROJECT_NAME} ${SOURCES})

# One translation unit against headers only — no Vulkan device, no Qt, no
# window, and nothing of the application linked in, so it costs a second and a
# half and cannot be the reason a build is slow. `EXCLUDE_FROM_ALL`: the normal
# build does not pay for it, `make check` and CI ask for it by name.
add_executable(video-code-tests EXCLUDE_FROM_ALL test/cpp/unit_test.cpp)
set_target_properties(video-code-tests PROPERTIES AUTOMOC OFF AUTOUIC OFF AUTORCC OFF)
target_include_directories(video-code-tests PRIVATE include)
# Qt6::Core and nothing more: the diff the agent pane draws is QStringList
# work, and linking Core alone costs a second where linking the application
# would cost fifteen. No MOC — this header has no Q_OBJECT in it.
target_link_libraries(video-code-tests PRIVATE nlohmann_json::nlohmann_json Qt6::Core)

if(APPLE)
    target_compile_definitions(${PROJECT_NAME} PRIVATE VK_USE_PLATFORM_METAL_EXT)
    target_link_libraries(${PROJECT_NAME} "-framework AppKit")
    set_target_properties(${PROJECT_NAME} PROPERTIES
        MACOSX_BUNDLE TRUE
        MACOSX_BUNDLE_BUNDLE_NAME "Video-Code"
        BUILD_RPATH "${MVK_PREFIX}/lib;${VCPKG_ROOT}/installed/${VCPKG_TARGET_TRIPLET}/lib"
        INSTALL_RPATH "${MVK_PREFIX}/lib;${VCPKG_ROOT}/installed/${VCPKG_TARGET_TRIPLET}/lib"
    )
elseif(UNIX AND NOT APPLE)
    # The Vulkan preview window presents through an XCB surface on Linux; the
    # widget pulls the X connection from Qt's xcb platform plugin.
    target_compile_definitions(${PROJECT_NAME} PRIVATE VK_USE_PLATFORM_XCB_KHR)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(XCB REQUIRED xcb)
    target_include_directories(${PROJECT_NAME} PRIVATE ${XCB_INCLUDE_DIRS})
    target_link_libraries(${PROJECT_NAME} ${XCB_LIBRARIES})
endif()

target_link_directories(${PROJECT_NAME} PRIVATE
    ${FFMPEG_LIBRARY_DIRS}
)

if(NOT APPLE)
    target_link_libraries(${PROJECT_NAME} stdc++fs)
endif()

target_compile_definitions(${PROJECT_NAME} PRIVATE
    FONT_DIR="${CMAKE_SOURCE_DIR}/assets/fonts"
    SHADER_DIR="${CMAKE_SOURCE_DIR}/assets/shaders"
    # The editor chrome is read from here at runtime, so a layout change costs a
    # reload rather than a rebuild. Point this at a qrc: URL to ship it inside
    # the binary instead.
    QML_DIR="${CMAKE_SOURCE_DIR}/qml"
)

target_link_libraries(${PROJECT_NAME}
    argparse::argparse
    nlohmann_json::nlohmann_json
    ${OpenCV_LIBS}
    ${FFMPEG_LIBRARIES}
    Qt6::Widgets
    Qt6::Core
    Qt6::Gui
    $<$<BOOL:${Qt6GuiPrivate_FOUND}>:Qt6::GuiPrivate>
    Qt6::Quick
    Qt6::Qml
    Qt6::QuickControls2

    pybind11::embed
    CURL::libcurl
    Vulkan::Vulkan
    glslang::glslang
    glslang::glslang-default-resource-limits
    glslang::SPIRV
    Freetype::Freetype
)

# A static Qt turns QML modules into static libraries: there is no plugin for the
# engine to discover at runtime, and an `import QtQuick` fails with "plugin
# qtquick2plugin not found" unless the plugin is linked in and its _init object
# registers it.  qt_import_qml_plugins() cannot work these out for us — it scans
# a target's own .qml files, and ours are read from disk at runtime — so the list
# is explicit.  Add a line here when a panel reaches for a module that is not yet
# in it.  A shared Qt (what CI installs) defines none of these targets and loads
# the plugins itself, so the whole list is skipped there.
if(NOT QT6_IS_SHARED_LIBS_BUILD)
    target_link_libraries(${PROJECT_NAME}
        Qt6::qtquick2plugin
        # QtQuick.Window is its own module: a panel torn out of the dock becomes
        # a real top-level window, and without this the import fails at runtime.
        Qt6::quickwindow
        # QtQml, for Instantiator: a Repeater only makes Items, and a floating
        # panel is a Window.
        Qt6::qmlplugin
        Qt6::qquicklayoutsplugin
        Qt6::qtquicktemplates2plugin
        Qt6::qtquickcontrols2plugin
        Qt6::qtquickcontrols2implplugin
        # The chrome paints its own look, so it asks for the Basic style rather
        # than the native macOS one, which would fight it (and drift between
        # machines).
        Qt6::qtquickcontrols2basicstyleplugin
        Qt6::qtquickcontrols2basicstyleimplplugin
    )
endif()

if(APPLE)
    target_link_libraries(${PROJECT_NAME}
        "-framework QuartzCore"
        "-framework AppKit"
    )
endif()
