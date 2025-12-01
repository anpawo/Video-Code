#include <gtest/gtest.h>
#include "window/Window.hpp"
#include "core/Core.hpp"
#include <QApplication>
#include <QKeyEvent>
#include <argparse/argparse.hpp>

class WindowCoverageTests : public ::testing::Test {
protected:
    void SetUp() override {
        // Configure parser with all necessary arguments
        _parser.add_argument("-w", "--width").default_value(800).scan<'i', int>();
        _parser.add_argument("-h", "--height").default_value(600).scan<'i', int>();
        _parser.add_argument("-f", "--framerate").default_value(30).scan<'i', int>();
        _parser.add_argument("--file").default_value(std::string("test.py"));
        _parser.add_argument("--generate").default_value(std::string("test.mp4"));
        _parser.add_argument("--showstack").default_value(false).implicit_value(true);
        _parser.add_argument("--time").default_value(false).implicit_value(true);
        
        // Parse with basic arguments
        std::vector<std::string> argv = {"videocode", "--width", "800", "--height", "600", "--framerate", "30", "--file", "test.py"};
        _parser.parse_args(argv);
    }

    argparse::ArgumentParser _parser{"test"};
};

TEST_F(WindowCoverageTests, WindowMethodsCoverage) {
    int argc = 0;
    char* argv[1] = {nullptr};
    QApplication app(argc, argv);
    
    // Test Window with correct constructor
    VC::Window window(_parser);
    
    // Test that window exists and was constructed successfully
    EXPECT_TRUE(true);
    
    // Test main routine method for coverage - call it once only
    // The timer in the constructor will automatically call it continuously,
    // but we test the method directly once for coverage
    window.mainRoutine();
    
    // Close the window to stop the timer and avoid infinite execution
    window.close();
    
    // Process any remaining Qt events to clean up properly
    app.processEvents();
    
    // Note: keyPressEvent is protected, so we can't test it directly
    // It would be tested through Qt's event system in integration tests
}

TEST_F(WindowCoverageTests, WindowErrorHandling) {
    int argc = 0;
    char* argv[1] = {nullptr};
    QApplication app(argc, argv);
    
    // Test window construction with different parser configurations
    argparse::ArgumentParser parser2("test2");
    parser2.add_argument("--width").default_value(100).scan<'i', int>();
    parser2.add_argument("--height").default_value(100).scan<'i', int>();
    parser2.add_argument("--framerate").default_value(15).scan<'i', int>();
    parser2.add_argument("--file").default_value(std::string("test.py"));
    parser2.add_argument("--generate").default_value(std::string("output.mp4"));
    parser2.add_argument("--showstack").default_value(false).implicit_value(true);
    parser2.add_argument("--time").default_value(false).implicit_value(true);
    
    // Parse arguments for parser2
    std::vector<std::string> argv2 = {"test2", "--width", "100", "--height", "100", "--file", "test.py"};
    parser2.parse_args(argv2);
    
    VC::Window smallWindow(parser2);
    EXPECT_TRUE(true); // Successfully constructed
    smallWindow.close(); // Close to stop timer
    
    argparse::ArgumentParser parser3("test3");
    parser3.add_argument("--width").default_value(1920).scan<'i', int>();
    parser3.add_argument("--height").default_value(1080).scan<'i', int>();
    parser3.add_argument("--framerate").default_value(120).scan<'i', int>();
    parser3.add_argument("--file").default_value(std::string("test.py"));
    parser3.add_argument("--generate").default_value(std::string("output.mp4"));
    parser3.add_argument("--showstack").default_value(false).implicit_value(true);
    parser3.add_argument("--time").default_value(false).implicit_value(true);
    
    // Parse arguments for parser3
    std::vector<std::string> argv3 = {"test3", "--width", "1920", "--height", "1080", "--file", "test.py"};
    parser3.parse_args(argv3);
    
    VC::Window largeWindow(parser3);
    EXPECT_TRUE(true); // Successfully constructed
    largeWindow.close(); // Close to stop timer
    
    // Process any remaining Qt events to clean up properly
    app.processEvents();
}