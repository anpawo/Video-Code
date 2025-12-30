#include <gtest/gtest.h>

#include <QApplication>
#include <QKeyEvent>
#include <argparse/argparse.hpp>

#include "core/Core.hpp"
#include "window/Window.hpp"

class WindowCoverageTests : public ::testing::Test
{
protected:

    void SetUp() override
    {
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
