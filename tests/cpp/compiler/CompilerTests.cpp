#include <gtest/gtest.h>
#include "compiler/Compiler.hpp"
#include "core/Core.hpp"

using namespace VC;

class CompilerTests : public ::testing::Test {
protected:
    void SetUp() override {
        // Create valid test arguments
        argv = {"videocode",
               "--width", "1920",
               "--height", "1080",
               "--framerate", "60",
               "--source", "test.json",
               "--output", "out.mp4"};
    }
    
    void initializeCore() {
        core = std::make_unique<Core>(static_cast<int>(argv.size()), 
                                    const_cast<char**>(argv.data()));
    }

    std::vector<std::string> argv;
    std::unique_ptr<Core> core;
};

TEST_F(CompilerTests, ValidConfigurationCompiles) {
    EXPECT_NO_THROW({
        initializeCore();
        Compiler compiler(*core);
    });
}

TEST_F(CompilerTests, BasicJsonCompilation) {
    initializeCore();
    Compiler compiler(*core);
    
    std::string validJson = R"({
        "inputs": [],
        "transformations": []
    })";
    
    EXPECT_NO_THROW(compiler.compile(validJson));
}

TEST_F(CompilerTests, MalformedJsonHandling) {
    initializeCore();
    Compiler compiler(*core);
    
    std::string invalidJson = "{ invalid json }";
    EXPECT_THROW(compiler.compile(invalidJson), std::exception);
}

TEST_F(CompilerTests, MissingRequiredFields) {
    initializeCore();
    Compiler compiler(*core);
    
    std::string missingInputs = R"({
        "transformations": []
    })";
    
    EXPECT_THROW(compiler.compile(missingInputs), std::exception);
}
