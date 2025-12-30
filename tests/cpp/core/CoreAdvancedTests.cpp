#include <gtest/gtest.h>

#include <argparse/argparse.hpp>
#include <fstream>

#include "core/Core.hpp"
#include "input/shape/Circle.hpp"
#include "input/shape/Rectangle.hpp"

using namespace VC;

class CoreAdvancedTests : public ::testing::Test
{
protected:

    void SetUp() override
    {
        // Use an existing test Python file
        testSceneFile = "/home/hippo/code/Video-Code/tests/python/test_videocode_core.py";

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
            .default_value(testSceneFile);
        parser.add_argument("--generate")
            .default_value("/tmp/test_output.mp4");
        parser.add_argument("--showstack")
            .default_value(false);
        parser.add_argument("--time")
            .default_value(false);

        std::vector<std::string> args = {"test-parser"};
        parser.parse_args(args);
    }

    void TearDown() override
    {
        std::remove("/tmp/test_output.mp4");
    }

    argparse::ArgumentParser parser{"test-parser"};
    std::string testSceneFile;
};

TEST_F(CoreAdvancedTests, PauseAndUnpause)
{
    Core core(parser);

    // Pause the core
    EXPECT_NO_THROW(core.pause());

    // Unpause
    EXPECT_NO_THROW(core.pause());
}

TEST_F(CoreAdvancedTests, NavigateFrames)
{
    Core core(parser);

    EXPECT_NO_THROW(core.goToFirstFrame());
    EXPECT_NO_THROW(core.goToLastFrame());
    EXPECT_NO_THROW(core.backward3frames());
    EXPECT_NO_THROW(core.forward3frames());
}

TEST_F(CoreAdvancedTests, GenerateVideoOutput)
{
    Core core(parser);

    // Generate video to exercise generateVideo path
    EXPECT_NO_THROW(core.generateVideo());
}
