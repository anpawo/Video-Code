cmake_minimum_required(VERSION 3.21)

project(video-code-tests LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)

# Find required packages
find_package(GTest CONFIG REQUIRED)
enable_testing()

# Create test executable
add_executable(video-code-tests
    # Core tests
    core/CoreTests.cpp
    core/FactoryTests.cpp
    core/CoreAdvancedTests.cpp

    # Input tests
    input/AInputTests.cpp
    input/AInputAdvancedTests.cpp
    input/FrameTests.cpp
    input/media/VideoTests.cpp
    input/shape/CircleTests.cpp
    input/shape/RectangleTests.cpp
    input/text/TextTests.cpp

    # Utils tests
    utils/ExceptionTests.cpp
    utils/StringTests.cpp
    utils/VectorTests.cpp

    # Window tests
    window/WindowTests.cpp
    window/WindowAdvancedTests.cpp
    
    # Additional single-header/source tests (added to ensure each public header has a direct test)
    compiler/CompilerTests.cpp
    transformation/TransformationTests.cpp
    transformation/FadeTests.cpp
    transformation/GrayscaleTests.cpp
    transformation/MoveToTests.cpp
    transformation/ZoomTests.cpp
    transformation/ScaleTests.cpp
    transformation/SetAlignTests.cpp
    transformation/SetArgumentTests.cpp
    utils/MapTests.cpp
    utils/DebugTests.cpp
    python/APITests.cpp
    input/IInputTests.cpp
    input/media/ImageTests.cpp
    input/text/FormulaTests.cpp
    input/text/CharTests.cpp
)

target_include_directories(video-code-tests PRIVATE
    ${CMAKE_SOURCE_DIR}/include
)

target_link_libraries(video-code-tests PRIVATE
    GTest::gtest
    GTest::gtest_main
    video-code-lib
    Qt6::Widgets
    Qt6::Core
    Qt6::Gui
)

include(GoogleTest)
gtest_discover_tests(video-code-tests)

# Enable coverage reporting
if(ENABLE_COVERAGE)
    target_compile_options(video-code-tests PRIVATE --coverage)
    target_link_options(video-code-tests PRIVATE --coverage)
endif()
