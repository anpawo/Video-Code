#include <gtest/gtest.h>
#include "core/Core.hpp"
#include "input/shape/Circle.hpp"
#include "input/shape/Rectangle.hpp"
#include <argparse/argparse.hpp>
#include <fstream>

using namespace VC;

class CoreAdvancedTests : public ::testing::Test {
protected:
    void SetUp() override {
        // Create a valid test scene JSON file
        testSceneFile = "/tmp/test_scene.json";
        std::ofstream outFile(testSceneFile);
        outFile << R"([
            {
                "action": "Create",
                "type": "Circle",
                "radius": 50,
                "color": [255, 0, 0, 255],
                "width": 200,
                "height": 200
            },
            {
                "action": "Add",
                "input": 0
            },
            {
                "action": "Apply",
                "input": 0,
                "transformation": "setPosition",
                "args": {
                    "x": 100,
                    "y": 100,
                    "duration": 0,
                    "start": 0
                }
            },
            {
                "action": "Wait",
                "n": 1
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
            .default_value("/tmp/test_output.mp4");
            
        std::vector<std::string> args = {"test-parser"};
        parser.parse_args(args);
    }

    void TearDown() override {
        std::remove(testSceneFile.c_str());
        std::remove("/tmp/test_output.mp4");
    }

    argparse::ArgumentParser parser{"test-parser"};
    std::string testSceneFile;
};

TEST_F(CoreAdvancedTests, PauseAndUnpause) {
    Core core(parser);
    
    // Pause the core
    EXPECT_NO_THROW(core.pause());
    
    // Unpause
    EXPECT_NO_THROW(core.pause());
}

TEST_F(CoreAdvancedTests, NavigateFrames) {
    Core core(parser);
    
    EXPECT_NO_THROW(core.goToFirstFrame());
    EXPECT_NO_THROW(core.goToLastFrame());
    EXPECT_NO_THROW(core.backward3frames());
    EXPECT_NO_THROW(core.forward3frames());
}

TEST_F(CoreAdvancedTests, GenerateVideoOutput) {
    Core core(parser);
    
    // Generate video to exercise generateVideo path
    EXPECT_NO_THROW(core.generateVideo());
}
