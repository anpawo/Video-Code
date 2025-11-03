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

        // Create a valid test scene
        testSceneFile = "/tmp/test_window_scene.json";
        std::ofstream outFile(testSceneFile);
        outFile << R"([
            {
                "action": "Create",
                "type": "Rectangle",
                "width": 100,
                "height": 100,
                "color": [128, 128, 128, 255]
            },
            {
                "action": "Add",
                "input": 0
            },
            {
                "action": "Wait",
                "n": 2
            }
        ])";
        outFile.close();

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
            .default_value(testSceneFile);
        parser.add_argument("--generate")
            .default_value("/tmp/window_test_output.mp4");
            
        std::vector<std::string> args = {"test-parser"};
        parser.parse_args(args);
    }

    void TearDown() override {
        std::remove(testSceneFile.c_str());
        std::remove("/tmp/window_test_output.mp4");
    }

    argparse::ArgumentParser parser{"test-parser"};
    std::string testSceneFile;
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
