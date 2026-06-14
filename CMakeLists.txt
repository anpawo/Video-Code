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
find_package(Qt6 REQUIRED COMPONENTS Widgets Core Gui)
find_package(CURL REQUIRED)
if(APPLE)
    execute_process(COMMAND brew --prefix molten-vk OUTPUT_VARIABLE MVK_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE)
    set(Vulkan_LIBRARY "${MVK_PREFIX}/lib/libMoltenVK.dylib")
    set(Vulkan_INCLUDE_DIR "${MVK_PREFIX}/libexec/include")
endif()
find_package(Vulkan REQUIRED)
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
    src/window/Window.cpp
    src/window/VulkanWidget.cpp

    # --- Vulkan ---
    src/vulkan/ShaderCompiler.cpp
    src/vulkan/VulkanHeadlessRenderer.cpp

    # --- Compiler ---
    src/compiler/Compiler.cpp

    # --- Test ---
    src/test/VisualTest.cpp

    # --- Core ---
    src/core/Core.cpp

    # --- Inputs ---
    src/input/AInput.cpp
    src/input/shape/BezierPath.cpp
    src/input/shape/Polygon.cpp
    src/input/text/Text.cpp
    src/input/media/Image.cpp
    src/input/media/Video.cpp

    # --- Fragment Shaders (GLSL-based, no C++ impl needed) ---
)

if(APPLE)
    list(APPEND SOURCES src/vulkan/MetalSurface.mm)
else()
    list(APPEND SOURCES src/vulkan/MetalSurfaceStub.cpp)
endif()

add_executable(${PROJECT_NAME} ${SOURCES})

if(APPLE)
    target_compile_definitions(${PROJECT_NAME} PRIVATE VK_USE_PLATFORM_METAL_EXT)
    set_target_properties(${PROJECT_NAME} PROPERTIES
        MACOSX_BUNDLE TRUE
        BUILD_RPATH "${MVK_PREFIX}/lib;${VCPKG_ROOT}/installed/${VCPKG_TARGET_TRIPLET}/lib"
        INSTALL_RPATH "${MVK_PREFIX}/lib;${VCPKG_ROOT}/installed/${VCPKG_TARGET_TRIPLET}/lib"
    )
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
)

target_link_libraries(${PROJECT_NAME}
    argparse::argparse
    nlohmann_json::nlohmann_json
    ${OpenCV_LIBS}
    ${FFMPEG_LIBRARIES}
    Qt6::Widgets
    Qt6::Core
    Qt6::Gui
    pybind11::embed
    CURL::libcurl
    Vulkan::Vulkan
    glslang::glslang
    glslang::glslang-default-resource-limits
    glslang::SPIRV
    Freetype::Freetype
)

if(APPLE)
    target_link_libraries(${PROJECT_NAME}
        "-framework QuartzCore"
        "-framework AppKit"
    )
endif()
