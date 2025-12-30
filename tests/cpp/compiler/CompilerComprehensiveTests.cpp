#include <gtest/gtest.h>

#include <argparse/argparse.hpp>
#include <fstream>

#include "compiler/Compiler.hpp"
#include "core/Core.hpp"

class CompilerComprehensiveTests : public ::testing::Test
{
protected:

    void SetUp() override
    {
        parser.add_argument("--width").default_value(640).scan<'i', int>();
        parser.add_argument("--height").default_value(480).scan<'i', int>();
        parser.add_argument("--framerate").default_value(30).scan<'i', int>();
        parser.add_argument("--file").default_value("/home/hippo/code/Video-Code/tests/python/simple_test.py");
        parser.add_argument("--generate").default_value("/tmp/compiler_test.mp4");
        parser.add_argument("--showstack").default_value(false);
        parser.add_argument("--time").default_value(false);

        std::vector<std::string> args = {"test"};
        parser.parse_args(args);
    }

    argparse::ArgumentParser parser{"test"};
};

TEST_F(CompilerComprehensiveTests, CompilerConstruction)
{
    // Test basic compiler construction
    EXPECT_NO_THROW(VC::Compiler compiler(parser));

    // Test that compiler properly initializes its core
    VC::Compiler compiler(parser);
    EXPECT_NO_THROW(compiler.generateVideo());
}

TEST_F(CompilerComprehensiveTests, GenerateVideoMethod)
{
    VC::Compiler compiler(parser);

    // Test video generation returns proper exit code
    int result = compiler.generateVideo();
    EXPECT_EQ(result, 0);
}

TEST_F(CompilerComprehensiveTests, CompilerWithDifferentSettings)
{
    // Test with different video settings
    argparse::ArgumentParser customParser{"test"};
    customParser.add_argument("--width").default_value(1280).scan<'i', int>();
    customParser.add_argument("--height").default_value(720).scan<'i', int>();
    customParser.add_argument("--framerate").default_value(60).scan<'i', int>();
    customParser.add_argument("--file").default_value("/home/hippo/code/Video-Code/tests/python/test_videocode_core.py");
    customParser.add_argument("--generate").default_value("/tmp/custom_compiler_test.mp4");
    customParser.add_argument("--showstack").default_value(true); // Enable showstack
    customParser.add_argument("--time").default_value(true);      // Enable timing

    std::vector<std::string> args = {"test"};
    customParser.parse_args(args);

    VC::Compiler customCompiler(customParser);
    EXPECT_NO_THROW(customCompiler.generateVideo());
}

TEST_F(CompilerComprehensiveTests, CompilerErrorPathsHandling)
{
    // Test with invalid output path
    argparse::ArgumentParser invalidParser{"test"};
    invalidParser.add_argument("--width").default_value(640).scan<'i', int>();
    invalidParser.add_argument("--height").default_value(480).scan<'i', int>();
    invalidParser.add_argument("--framerate").default_value(30).scan<'i', int>();
    invalidParser.add_argument("--file").default_value("nonexistent.py");
    invalidParser.add_argument("--generate").default_value("/invalid/path/test.mp4");
    invalidParser.add_argument("--showstack").default_value(false);
    invalidParser.add_argument("--time").default_value(false);

    std::vector<std::string> args = {"test"};
    invalidParser.parse_args(args);

    VC::Compiler invalidCompiler(invalidParser);

    // Should not throw even with invalid paths - the implementation handles errors gracefully
    EXPECT_NO_THROW(invalidCompiler.generateVideo());
}

TEST_F(CompilerComprehensiveTests, MultipleCompilerInstances)
{
    // Test creating multiple compiler instances
    VC::Compiler compiler1(parser);
    VC::Compiler compiler2(parser);
    VC::Compiler compiler3(parser);

    // Each should work independently
    EXPECT_NO_THROW(compiler1.generateVideo());
    EXPECT_NO_THROW(compiler2.generateVideo());
    EXPECT_NO_THROW(compiler3.generateVideo());
}

TEST_F(CompilerComprehensiveTests, CompilerDestructorCoverage)
{
    {
        // Create compiler in local scope to test destructor
        VC::Compiler compiler(parser);
        compiler.generateVideo();
    } // Destructor should be called here

    // If we reach here, destructor executed successfully
    SUCCEED();
}

TEST_F(CompilerComprehensiveTests, CompilerWithMinimalSettings)
{
    // Test with minimal video settings
    argparse::ArgumentParser minimalParser{"test"};
    minimalParser.add_argument("--width").default_value(64).scan<'i', int>(); // Very small
    minimalParser.add_argument("--height").default_value(64).scan<'i', int>();
    minimalParser.add_argument("--framerate").default_value(1).scan<'i', int>(); // 1 FPS
    minimalParser.add_argument("--file").default_value("/home/hippo/code/Video-Code/tests/python/test_videocode_core.py");
    minimalParser.add_argument("--generate").default_value("/tmp/minimal_test.mp4");
    minimalParser.add_argument("--showstack").default_value(false);
    minimalParser.add_argument("--time").default_value(false);

    std::vector<std::string> args = {"test"};
    minimalParser.parse_args(args);

    VC::Compiler minimalCompiler(minimalParser);
    EXPECT_EQ(minimalCompiler.generateVideo(), 0);
}
