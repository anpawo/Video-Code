#include <gtest/gtest.h>
#include "compiler/Compiler.hpp"
#include "core/Core.hpp"

using namespace VC;

class CompilerTests : public ::testing::Test {
protected:
    void SetUp() override {
        parser.add_argument("--width")
            .default_value("1920")
            .scan<'i', int>();
        parser.add_argument("--height")
            .default_value("1080")
            .scan<'i', int>();
        parser.add_argument("--framerate")
            .default_value("60")
            .scan<'i', int>();
        parser.add_argument("--sourceFile")
            .default_value(std::string("test.json"));
        parser.add_argument("--generate")
            .default_value(std::string("out.mp4"));
            
        std::vector<std::string> args = {"test-parser"};
        parser.parse_args(args);
    }
    
    argparse::ArgumentParser parser{"test-parser"};

    std::vector<std::string> argv;
    std::unique_ptr<Core> core;
};

TEST_F(CompilerTests, ValidConfigurationCompiles) {
    EXPECT_NO_THROW({
        Compiler compiler(parser);
    });
}

TEST_F(CompilerTests, BasicGeneration) {
    Compiler compiler(parser);
    
    std::string validJson = R"({
        "inputs": [],
        "transformations": []
    })";
    
    EXPECT_NO_THROW(compiler.generateVideo());
}

TEST_F(CompilerTests, InvalidConfiguration) {
    // Create new parser with invalid output path
    argparse::ArgumentParser customParser{"test-parser"};
    customParser.add_argument("--width")
        .default_value("1920")
        .scan<'i', int>();
    customParser.add_argument("--height")
        .default_value("1080")
        .scan<'i', int>();
    customParser.add_argument("--framerate")
        .default_value("60")
        .scan<'i', int>();
        customParser.add_argument("--sourceFile")
            .default_value(std::string("test.json"));
        customParser.add_argument("--generate")
            .default_value(std::string("/nonexistent/path/out.mp4"));    std::vector<std::string> args = {"test-parser"};
    customParser.parse_args(args);

    Compiler compiler(customParser);
    EXPECT_THROW(compiler.generateVideo(), std::exception);
}

TEST_F(CompilerTests, MissingSourceFile) {
    // Create new parser with nonexistent source file
    argparse::ArgumentParser customParser{"test-parser"};
    customParser.add_argument("--width")
        .default_value("1920")
        .scan<'i', int>();
    customParser.add_argument("--height")
        .default_value("1080")
        .scan<'i', int>();
    customParser.add_argument("--framerate")
        .default_value("60")
        .scan<'i', int>();
        customParser.add_argument("--sourceFile")
            .default_value(std::string("nonexistent.json"));
        customParser.add_argument("--generate")
            .default_value(std::string("out.mp4"));    std::vector<std::string> args = {"test-parser"};
    customParser.parse_args(args);

    Compiler compiler(customParser);
    EXPECT_THROW(compiler.generateVideo(), std::exception);
}
