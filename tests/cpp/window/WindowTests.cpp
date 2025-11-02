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
        parser.add_argument("--sourceFile")
            .required()
            .default_value("/home/hippo/code/Video-Code/build/tests/resources/test_video.mp4");
            
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
    EXPECT_EQ(window.width(), 640);
    EXPECT_EQ(window.height(), 480);
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

    std::vector<std::string> args = {"test-parser"};
    customParser.parse_args(args);

    Window window(customParser);
    EXPECT_EQ(window.width(), 800);
    EXPECT_EQ(window.height(), 600);
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

    std::vector<std::string> args = {"test-parser"};
    customParser.parse_args(args);

    Window window(customParser);
    window.mainRoutine(); // Should initialize with 60fps timer
}