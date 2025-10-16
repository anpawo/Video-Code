cmake_minimum_required(VERSION 3.21)
project(video-code VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wno-deprecated -pipe -O2 -D_REENTRANT -DVC_DEBUG_ON -DQT_NO_DEBUG -DQT_WIDGETS_LIB -DQT_GUI_LIB -DQT_CORE_LIB -DQT_NO_KEYWORDS")

if(DEBUG)
    message(STATUS "Debug build")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g3")
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
        set(VCPKG_TARGET_TRIPLET "x64-windows")
    elseif(UNIX AND NOT APPLE)
        set(VCPKG_TARGET_TRIPLET "x64-linux")
    elseif(APPLE)
        set(VCPKG_TARGET_TRIPLET "x64-osx")
    endif()
endif()

set(CMAKE_PREFIX_PATH "${CMAKE_PREFIX_PATH};${CMAKE_SOURCE_DIR}/vcpkg_installed/${VCPKG_TARGET_TRIPLET}")

if(NOT DEFINED ENV{Qt6_DIR})
    set(Qt6_DIR "/usr/include/qt6/6.8.2/gcc_64/lib/cmake/Qt6")
endif()

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
endif()

find_package(OpenCV REQUIRED)
find_package(Python3 3.12 REQUIRED COMPONENTS Development Development.Module Development.Embed)
find_package(Qt6 REQUIRED COMPONENTS Widgets Core Gui)

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
)

set(SOURCES
    # --- Main ---
    src/Main.cpp

    # --- Window ---
    include/window/Window.hpp # Needed for the MOC (Meta-Object Compiler) Q_OBJECT
    src/window/Window.cpp

    # --- Compiler ---
    src/compiler/Compiler.cpp

    # --- Core ---
    src/core/Core.cpp

    # --- Inputs ---
    src/input/AInput.cpp
    # Media
    src/input/media/Image.cpp
    src/input/media/Video.cpp
    # Text
    src/input/text/Text.cpp
    # Shape
    src/input/shape/Circle.cpp
    src/input/shape/Rectangle.cpp

    # --- Transformation ---
    # Setter
    src/transformation/setter/setPosition.cpp
    src/transformation/setter/setAlign.cpp
    src/transformation/setter/setArgument.cpp
    # src/transformation/setter/setOpacity.cpp
    # Position
    src/transformation/position/moveTo.cpp
    # Color
    src/transformation/color/fade.cpp
    src/transformation/color/grayscale.cpp
    # Other
    src/transformation/size/zoom.cpp
    src/transformation/size/scale.cpp

)

add_executable(${PROJECT_NAME} ${SOURCES})

target_link_directories(${PROJECT_NAME} PRIVATE
    ${FFMPEG_LIBRARY_DIRS}
)

target_link_libraries(${PROJECT_NAME}
    argparse::argparse
    nlohmann_json::nlohmann_json
    ${OpenCV_LIBS}
    ${FFMPEG_LIBRARIES}
    Qt6::Widgets
    Qt6::Core
    Qt6::Gui
    stdc++fs
    Python3::Python
)
