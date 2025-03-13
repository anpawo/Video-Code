cmake_minimum_required(VERSION 3.21)
project(video-code VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wno-deprecated -pipe -O2 -D_REENTRANT -DVC_DEBUG_ON -DQT_NO_DEBUG -DQT_WIDGETS_LIB -DQT_GUI_LIB -DQT_CORE_LIB -DQT_NO_KEYWORDS")

set(VCPKG_BUILD_TYPE "release")

if (NOT DEFINED ENV{CMAKE_BINARY_DIR})
    set(CMAKE_BINARY_DIR "${CMAKE_SOURCE_DIR}/build")
endif()

# if(NOT DEFINED ENV{VCPKG_ROOT})
#     message(STATUS "Downloading vcpkg...")
#     execute_process(COMMAND git clone https://github.com/microsoft/vcpkg.git ${CMAKE_BINARY_DIR}/vcpkg)
#     if (WIN32)
#         execute_process(COMMAND ${CMAKE_BINARY_DIR}/vcpkg/bootstrap-vcpkg.bat) # Windows
#     else()
#         execute_process(COMMAND ${CMAKE_BINARY_DIR}/vcpkg/bootstrap-vcpkg.sh)  # Linux/macOS
#     endif()
#     set(VCPKG_ROOT "${CMAKE_BINARY_DIR}/vcpkg")
# else()
#     set(VCPKG_ROOT $ENV{VCPKG_ROOT})
# endif()

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

message(STATUS "VCPKG_ROOT: ${VCPKG_ROOT}")
message(STATUS "VCPKG_TARGET_TRIPLET: ${VCPKG_TARGET_TRIPLET}")
if (EXISTS "${CMAKE_SOURCE_DIR}/vcpkg.json")
    message(STATUS "Found vcpkg.json, installing only missing dependencies from manifest")
    execute_process(
        COMMAND "${VCPKG_ROOT}/vcpkg" install --triplet ${VCPKG_TARGET_TRIPLET} --recurse
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}/build"
    )
endif()

message(STATUS "all vcpkg packages installed")

if (UNIX AND NOT APPLE)
    find_package(X11)
    if (NOT X11_Xi_FOUND OR NOT X11_Xtst_FOUND)
        message(WARNING "You must install libxi-dev and libxtst-dev on Linux.\nrun : apt-get install libxi-dev libxtst-dev")
    endif()
endif()

find_package(OpenCV REQUIRED)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
find_package(Qt6 REQUIRED COMPONENTS Widgets Core Gui)

include_directories(
    ${OpenCV_INCLUDE_DIRS}
    ${Python3_INCLUDE_DIRS}
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
    ${OpenCV_LIBS}
    ${Python3_LIBRARIES}
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
