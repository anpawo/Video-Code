#include <gtest/gtest.h>
#include "window/Window.hpp"
#include "input/Frame.hpp"
#include <QApplication>
#include <QImage>

using namespace VC;

class WindowTests : public ::testing::Test {
protected:
    WindowTests() : testFrame(cv::Mat(480, 640, CV_8UC3, cv::Scalar(255, 0, 0))) {}

    void SetUp() override {
        // Ensure we have a QApplication instance for the tests
        if (!qApp) {
            static int argc = 1;
            static char* argv[] = { (char*)"dummy" };
            new QApplication(argc, argv);
        }

        parser.add_argument("--width")
            .default_value(640)
            .scan<'i', int>();
        parser.add_argument("--height")
            .default_value(480)
            .scan<'i', int>();
        parser.add_argument("--framerate")
            .default_value(30)
            .scan<'i', int>();
        parser.add_argument("--file")
            .default_value("/home/hippo/code/Video-Code/tests/python/test_videocode_core.py");
        parser.add_argument("--generate")
            .default_value("out.mp4");
        parser.add_argument("--showstack")
            .default_value(false);
        parser.add_argument("--time")
            .default_value(false);
            
        std::vector<std::string> args = {"test-parser"};
        parser.parse_args(args);
    }

    argparse::ArgumentParser parser{"test-parser"};
    Frame testFrame;
};

TEST_F(WindowTests, ConstructorInitialization) {
    // Check Qt environment
    EXPECT_NE(qApp, nullptr);
    
    // Create window with test parser
    Window window(parser);
    // Window resizes itself to half the provided dimensions in constructor
    EXPECT_EQ(window.width(), 640 / 2);
    EXPECT_EQ(window.height(), 480 / 2);
}

TEST_F(WindowTests, CoreInteraction) {
    Window window(parser);
    
    // Test window routine can run
    EXPECT_NO_THROW(window.mainRoutine());
}

TEST_F(WindowTests, CustomDimensions) {
    // Create new parser with custom dimensions
    argparse::ArgumentParser customParser{"test-parser"};
    customParser.add_argument("--width")
        .default_value(800)
        .scan<'i', int>();
    customParser.add_argument("--height")
        .default_value(600)
        .scan<'i', int>();
    customParser.add_argument("--framerate")  // Add required framerate arg
        .default_value(30)
        .scan<'i', int>();
    // Add missing args expected by Core
    customParser.add_argument("--file")
        .default_value("/home/hippo/code/Video-Code/tests/python/test_videocode_core.py");
    customParser.add_argument("--generate")
        .default_value("out.mp4");
    customParser.add_argument("--showstack")
        .default_value(false);
    customParser.add_argument("--time")
        .default_value(false);

    std::vector<std::string> args = {"test-parser"};
    customParser.parse_args(args);

    Window window(customParser);
    // window resizes to half the given dimensions
    EXPECT_EQ(window.width(), 800 / 2);
    EXPECT_EQ(window.height(), 600 / 2);
}

TEST_F(WindowTests, Framerate) {
    // Create new parser with custom framerate
    argparse::ArgumentParser customParser{"test-parser"};
    customParser.add_argument("--width")
        .default_value(640)
        .scan<'i', int>();
    customParser.add_argument("--height")
        .default_value(480)
        .scan<'i', int>();
    customParser.add_argument("--framerate")
        .default_value(60)  // Test with 60fps
        .scan<'i', int>();
    // Add missing args expected by Core
    customParser.add_argument("--file")
        .default_value("/home/hippo/code/Video-Code/tests/python/test_videocode_core.py");
    customParser.add_argument("--generate")
        .default_value("out.mp4");
    customParser.add_argument("--showstack")
        .default_value(false);
    customParser.add_argument("--time")
        .default_value(false);

    std::vector<std::string> args = {"test-parser"};
    customParser.parse_args(args);

    Window window(customParser);
    window.mainRoutine(); // Should initialize with 60fps timer
}