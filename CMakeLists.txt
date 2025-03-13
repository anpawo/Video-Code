cmake_minimum_required(VERSION 3.21)
project(video-code VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wno-deprecated -pipe -O2 -D_REENTRANT -DVC_DEBUG_ON -DQT_NO_DEBUG -DQT_WIDGETS_LIB -DQT_GUI_LIB -DQT_CORE_LIB -DQT_NO_KEYWORDS")

set(VCPKG_BUILD_TYPE "release")

if (NOT DEFINED ENV{CMAKE_BINARY_DIR})
    set(CMAKE_BINARY_DIR "${CMAKE_SOURCE_DIR}/build")
endif()

include(FetchContent)
FetchContent_Declare(
    CPM
    GIT_REPOSITORY https://github.com/cpm-cmake/CPM.cmake
    GIT_TAG c1bca7badb2293f606a24a94d4ac708659f86e6a
)
FetchContent_MakeAvailable(CPM)

CPMAddPackage(
    NAME argparse
    GITHUB p-ranav/argparse
    VERSION 2.9
)

CPMAddPackage(
    NAME nlohmann-json
    GITHUB nlohmann/json
    VERSION 3.11.2
)

find_package(OpenCV REQUIRED)
find_package(Qt6 REQUIRED COMPONENTS Widgets Core Gui)

include_directories(
    ${OpenCV_INCLUDE_DIRS}
    include
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
)

add_executable(${PROJECT_NAME} ${SOURCES})

target_link_libraries(${PROJECT_NAME}
    argparse::argparse
    nlohmann_json::nlohmann_json
    ${OpenCV_LIBS}
    Qt6::Widgets
    Qt6::Core
    Qt6::Gui
)

add_custom_target(format
    COMMAND clang-format -i ${CMAKE_SOURCE_DIR}/**/*.cpp ${CMAKE_SOURCE_DIR}/**/*.hpp
)

add_custom_target(docs
    COMMAND ${CMAKE_SOURCE_DIR}/vc --generate
    COMMAND ${CMAKE_SOURCE_DIR}/docs/readme/generate.sh
)
