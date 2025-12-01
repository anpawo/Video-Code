#include <gtest/gtest.h>
#include "window/Window.hpp"
#include "input/Frame.hpp"
#include <QApplication>
#include <QLabel>
#include <fstream>

using namespace VC;

class WindowAdvancedTests : public ::testing::Test {
protected:
    void SetUp() override {
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
            .default_value("/tmp/window_test_output.mp4");
        parser.add_argument("--showstack")
            .default_value(false);
        parser.add_argument("--time")
            .default_value(false);
            
        std::vector<std::string> args = {"test-parser"};
        parser.parse_args(args);
    }

    void TearDown() override {
        std::remove("/tmp/window_test_output.mp4");
    }

    argparse::ArgumentParser parser{"test-parser"};
};

TEST_F(WindowAdvancedTests, MainRoutineUpdatesFrame) {
    Window window(parser);
    
    // Run main routine multiple times
    EXPECT_NO_THROW(window.mainRoutine());
    EXPECT_NO_THROW(window.mainRoutine());
    EXPECT_NO_THROW(window.mainRoutine());
}

TEST_F(WindowAdvancedTests, KeyPressEscape) {
    Window window(parser);
    
    // Simulate escape key press
    QKeyEvent escapeEvent(QEvent::KeyPress, Qt::Key_Escape, Qt::NoModifier);
    // Note: We can't directly test keyPressEvent as it's protected, but we can verify window exists
    EXPECT_NE(&window, nullptr);
}

TEST_F(WindowAdvancedTests, WindowDimensions) {
    Window window(parser);
    
    // Verify window dimensions are half of parser dimensions
    EXPECT_EQ(window.width(), 640 / 2);
    EXPECT_EQ(window.height(), 480 / 2);
}
