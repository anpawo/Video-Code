cmake_minimum_required(VERSION 3.21)
project(video_code_tests LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG release-1.11.0
)
FetchContent_MakeAvailable(googletest)

find_package(OpenCV REQUIRED)

add_subdirectory(.. ${CMAKE_BINARY_DIR}/video-code)

include_directories(${OpenCV_INCLUDE_DIRS}
    ${CMAKE_SOURCE_DIR}/../include
    ${CMAKE_SOURCE_DIR}/../include/vm
)

set(TEST_SOURCES
    unit/fade.cpp
    unit/move.cpp
    unit/translate.cpp
    unit/main.cpp
)

set(SOURCE_FILES
    ${CMAKE_SOURCE_DIR}/../src/transformation/color/fade.cpp
    ${CMAKE_SOURCE_DIR}/../src/transformation/position/move.cpp
    ${CMAKE_SOURCE_DIR}/../src/transformation/position/translate.cpp
    ${CMAKE_SOURCE_DIR}/../src/transformation/other/merge.cpp
    ${CMAKE_SOURCE_DIR}/../src/input/concrete/ABCConcreteInput.cpp
    ${CMAKE_SOURCE_DIR}/../src/transformation/other/overlay.cpp
    ${CMAKE_SOURCE_DIR}/../src/transformation/other/repeat.cpp
    ${CMAKE_SOURCE_DIR}/../src/input/concrete/media/Image.cpp
    ${CMAKE_SOURCE_DIR}/../src/input/concrete/media/Video.cpp
    ${CMAKE_SOURCE_DIR}/../src/input/concrete/text/Text.cpp
    ${CMAKE_SOURCE_DIR}/../src/input/composite/Slice.cpp
    ${CMAKE_SOURCE_DIR}/../src/vm/Register.cpp
)

add_executable(runTests ${TEST_SOURCES} ${SOURCE_FILES})

target_link_libraries(runTests gtest gtest_main ${OpenCV_LIBS} nlohmann_json::nlohmann_json fmt::fmt)

enable_testing()

add_test(NAME runTests COMMAND runTests)
