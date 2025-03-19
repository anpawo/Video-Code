cmake_minimum_required(VERSION 3.21)
project(video-code VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++20 -Wall -Wextra -Wno-deprecated -pipe -O2 -D_REENTRANT -DVC_DEBUG_ON -DQT_NO_DEBUG -DQT_WIDGETS_LIB -DQT_GUI_LIB -DQT_CORE_LIB -DQT_NO_KEYWORDS")

set_property(GLOBAL PROPERTY CXX_STANDARD 20)

if (UNIX AND NOT APPLE)
    set(CMAKE_CXX_COMPILER "g++-13")
endif()

if (NOT DEFINED ENV{VCPKG_ROOT})
    message(FATAL_ERROR "VCPKG_ROOT environment variable not set")
endif()

set(VCPKG_ROOT $ENV{VCPKG_ROOT})
set(CMAKE_TOOLCHAIN_FILE "${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake" CACHE STRING "Vcpkg toolchain file")
set(VCPKG_FEATURE_FLAGS "manifests")

if(NOT DEFINED VCPKG_TARGET_TRIPLET)
    if (WIN32)
        set(VCPKG_TARGET_TRIPLET "x64-windows")
    elseif (UNIX AND NOT APPLE)
        set(VCPKG_TARGET_TRIPLET "x64-linux")
    elseif (APPLE)
        set(VCPKG_TARGET_TRIPLET "x64-osx")
    endif()
endif()
set(CMAKE_PREFIX_PATH "${CMAKE_PREFIX_PATH};${CMAKE_SOURCE_DIR}/vcpkg_installed/${VCPKG_TARGET_TRIPLET}")

if (NOT DEFINED ENV{Qt6_DIR})
    set(Qt6_DIR "/usr/include/qt6/6.8.2/gcc_64/lib/cmake/Qt6")
endif()

find_package(OpenCV REQUIRED)
find_package(Python3 3.12 REQUIRED COMPONENTS Development Development.Module Development.Embed)
find_package(Qt6 REQUIRED COMPONENTS Widgets Core Gui)
find_package(nlohmann_json CONFIG REQUIRED)
set(argparse_DIR "${VCPKG_ROOT}/installed/${VCPKG_TARGET_TRIPLET}/share/argparse")
find_package(argparse CONFIG REQUIRED)

include_directories(
    ${OpenCV_INCLUDE_DIRS}
    ${CMAKE_SOURCE_DIR}/include
    ${Python3_INCLUDE_DIRS}
)

set(SOURCES
    src/Main.cpp
    src/vm/VideoCode.cpp
    src/vm/Register.cpp
    src/vm/AppWindow.cpp
    src/vm/AppEvent.cpp
    src/compiler/generateVideo.cpp
    src/input/concrete/ABCConcreteInput.cpp
    src/input/concrete/media/Image.cpp
    src/input/concrete/media/Video.cpp
    src/input/concrete/text/Text.cpp
    src/input/composite/Slice.cpp
    src/transformation/position/translate.cpp
    src/transformation/position/move.cpp
    src/transformation/color/fade.cpp
    src/transformation/color/grayscale.cpp
    src/transformation/other/overlay.cpp
    src/transformation/other/repeat.cpp
)

add_executable(${PROJECT_NAME} ${SOURCES})

target_link_libraries(${PROJECT_NAME}
    argparse::argparse
    nlohmann_json::nlohmann_json
    ${OpenCV_LIBS}
    Qt6::Widgets
    Qt6::Core
    Qt6::Gui
    stdc++fs
    Python3::Python
)
