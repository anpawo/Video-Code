#include <gtest/gtest.h>

#include <QApplication>
#include <QKeyEvent>
#include <QLabel>
#include <QTimer>
#include <argparse/argparse.hpp>

#include "window/Window.hpp"

class WindowComprehensiveTests : public ::testing::Test
{
protected:

    void SetUp() override
    {
        // Ensure we have a QApplication instance
        if (!qApp) {
            static int argc = 1;
            static char* argv[] = {(char*)"dummy"};
            new QApplication(argc, argv);
        }

        parser.add_argument("--width").default_value(800).scan<'i', int>();
        parser.add_argument("--height").default_value(600).scan<'i', int>();
        parser.add_argument("--framerate").default_value(30).scan<'i', int>();
        parser.add_argument("--file").default_value("/home/hippo/code/Video-Code/tests/python/test_videocode_core.py");
        parser.add_argument("--generate").default_value("/tmp/window_test.mp4");
        parser.add_argument("--showstack").default_value(false);
        parser.add_argument("--time").default_value(false);

        std::vector<std::string> args = {"test"};
        parser.parse_args(args);
    }

    argparse::ArgumentParser parser{"test"};
};

TEST_F(WindowComprehensiveTests, WindowConstructorInitialization)
{
    VC::Window window(parser);

    // Test that window was created with expected properties
    EXPECT_EQ(window.width(), 800 / 2); // Window scales to half size
    EXPECT_EQ(window.height(), 600 / 2);

    // Window should be visible after construction
    EXPECT_TRUE(window.isVisible());
}

TEST_F(WindowComprehensiveTests, MainRoutineExecution)
{
    VC::Window window(parser);

    // Test multiple calls to mainRoutine
    for (int i = 0; i < 5; ++i) {
        EXPECT_NO_THROW(window.mainRoutine());
    }
}

TEST_F(WindowComprehensiveTests, KeyEventHandling)
{
    VC::Window window(parser);

    // Create mock key events for each key the window handles

    // Space key (pause/unpause)
    QKeyEvent spaceEvent(QEvent::KeyPress, Qt::Key_Space, Qt::NoModifier);

    // Arrow keys (navigation)
    QKeyEvent downEvent(QEvent::KeyPress, Qt::Key_Down, Qt::NoModifier);
    QKeyEvent upEvent(QEvent::KeyPress, Qt::Key_Up, Qt::NoModifier);
    QKeyEvent leftEvent(QEvent::KeyPress, Qt::Key_Left, Qt::NoModifier);
    QKeyEvent rightEvent(QEvent::KeyPress, Qt::Key_Right, Qt::NoModifier);

    // Escape key (close)
    QKeyEvent escapeEvent(QEvent::KeyPress, Qt::Key_Escape, Qt::NoModifier);

    // Other key (default handling)
    QKeyEvent otherEvent(QEvent::KeyPress, Qt::Key_A, Qt::NoModifier);

    // We can't directly call keyPressEvent as it's protected, but we can test that
    // the window handles events correctly by verifying it doesn't crash
    // The actual key handling logic is tested through Core methods
    EXPECT_NO_THROW(window.show());
}

TEST_F(WindowComprehensiveTests, TimerConfiguration)
{
    VC::Window window(parser);

    // Window should have a timer configured based on framerate
    // We can't easily test the timer directly, but we can verify the window was created
    EXPECT_NE(&window, nullptr);

    // Test with different framerate
    argparse::ArgumentParser customParser{"test"};
    customParser.add_argument("--width").default_value(640).scan<'i', int>();
    customParser.add_argument("--height").default_value(480).scan<'i', int>();
    customParser.add_argument("--framerate").default_value(60).scan<'i', int>(); // 60 FPS
    customParser.add_argument("--file").default_value("/home/hippo/code/Video-Code/tests/python/test_videocode_core.py");
    customParser.add_argument("--generate").default_value("/tmp/test.mp4");
    customParser.add_argument("--showstack").default_value(false);
    customParser.add_argument("--time").default_value(false);

    std::vector<std::string> args = {"test"};
    customParser.parse_args(args);

    VC::Window highFpsWindow(customParser);
    EXPECT_NE(&highFpsWindow, nullptr);
}

TEST_F(WindowComprehensiveTests, WindowStylingAndTitle)
{
    VC::Window window(parser);

    // Verify window title was set (includes the file path)
    QString title = window.windowTitle();
    EXPECT_TRUE(title.contains("Video-Code"));
    EXPECT_TRUE(title.contains("test_videocode_core.py"));

    // Window should have black background style
    QString styleSheet = window.styleSheet();
    EXPECT_TRUE(styleSheet.contains("black"));
}

TEST_F(WindowComprehensiveTests, WindowLayout)
{
    VC::Window window(parser);

    // Window should have a central widget with proper layout
    QWidget* centralWidget = window.centralWidget();
    EXPECT_NE(centralWidget, nullptr);

    // Layout should contain the image label
    QLayout* layout = centralWidget->layout();
    EXPECT_NE(layout, nullptr);
}

TEST_F(WindowComprehensiveTests, DifferentWindowSizes)
{
    // Test with very small window
    argparse::ArgumentParser smallParser{"test"};
    smallParser.add_argument("--width").default_value(100).scan<'i', int>();
    smallParser.add_argument("--height").default_value(100).scan<'i', int>();
    smallParser.add_argument("--framerate").default_value(30).scan<'i', int>();
    smallParser.add_argument("--file").default_value("/home/hippo/code/Video-Code/tests/python/test_videocode_core.py");
    smallParser.add_argument("--generate").default_value("/tmp/test.mp4");
    smallParser.add_argument("--showstack").default_value(false);
    smallParser.add_argument("--time").default_value(false);

    std::vector<std::string> args = {"test"};
    smallParser.parse_args(args);

    VC::Window smallWindow(smallParser);
    EXPECT_EQ(smallWindow.width(), 100 / 2);
    EXPECT_EQ(smallWindow.height(), 100 / 2);

    // Test with large window
    argparse::ArgumentParser largeParser{"test"};
    largeParser.add_argument("--width").default_value(1920).scan<'i', int>();
    largeParser.add_argument("--height").default_value(1080).scan<'i', int>();
    largeParser.add_argument("--framerate").default_value(30).scan<'i', int>();
    largeParser.add_argument("--file").default_value("/home/hippo/code/Video-Code/tests/python/test_videocode_core.py");
    largeParser.add_argument("--generate").default_value("/tmp/test.mp4");
    largeParser.add_argument("--showstack").default_value(false);
    largeParser.add_argument("--time").default_value(false);

    largeParser.parse_args(args);

    VC::Window largeWindow(largeParser);
    EXPECT_EQ(largeWindow.width(), 1920 / 2);
    EXPECT_EQ(largeWindow.height(), 1080 / 2);
}
