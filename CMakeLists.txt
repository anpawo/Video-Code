cmake_minimum_required(VERSION 3.21)
project(video-code VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wno-deprecated -pipe -O2 -D_REENTRANT -DVC_DEBUG_ON -DQT_NO_DEBUG -DQT_WIDGETS_LIB -DQT_GUI_LIB -DQT_CORE_LIB -DQT_NO_KEYWORDS")

if (CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")
endif()

if (NOT DEFINED ENV{CMAKE_BINARY_DIR})
    set(CMAKE_BINARY_DIR "${CMAKE_SOURCE_DIR}/build")
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
set(CMAKE_PREFIX_PATH "${VCPKG_ROOT}/installed/${VCPKG_TARGET_TRIPLET}")

if (UNIX AND NOT APPLE)
    find_package(X11)
    if (NOT X11_Xi_FOUND OR NOT X11_Xtst_FOUND)
        message(WARNING "You must install libxi-dev and libxtst-dev on Linux.\nrun : apt-get install libxi-dev libxtst-dev")
    endif()
endif()

if (NOT DEFINED ENV{Qt6_DIR})
    set(Qt6_DIR "/usr/include/qt6/6.8.2/gcc_64/lib/cmake/Qt6")
endif()

find_package(OpenCV REQUIRED)
find_package(Python3 3.12 REQUIRED COMPONENTS Development Development.Module Development.Embed)
find_package(Qt6 REQUIRED COMPONENTS Widgets Core Gui)

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

FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 8.0.1
)
FetchContent_MakeAvailable(fmt)

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
    src/transformation/other/overlay.cpp
    src/transformation/other/repeat.cpp
    src/transformation/other/zoom.cpp
)

add_executable(${PROJECT_NAME} ${SOURCES})

target_link_libraries(${PROJECT_NAME}
    argparse::argparse
    nlohmann_json::nlohmann_json
    ${OpenCV_LIBS}
    Qt6::Widgets
    Qt6::Core
    Qt6::Gui
    fmt::fmt
    stdc++fs
    Python3::Python
)

add_custom_target(format
    COMMAND clang-format -i ${CMAKE_SOURCE_DIR}/**/*.cpp ${CMAKE_SOURCE_DIR}/**/*.hpp
)

add_custom_target(docs
    COMMAND ${CMAKE_SOURCE_DIR}/vc --generate
    COMMAND ${CMAKE_SOURCE_DIR}/docs/readme/generate.sh
)
