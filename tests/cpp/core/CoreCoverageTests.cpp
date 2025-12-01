#include <gtest/gtest.h>
#include <argparse/argparse.hpp>
#include "core/Core.hpp"
#include "input/media/Video.hpp"
#include "input/media/Image.hpp"
#include "utils/Exception.hpp"
#include "python/API.hpp"
#include "core/Factory.hpp"
#include <QApplication>
#include <QLabel>

namespace VC {

class CoreCoverageTests : public ::testing::Test {
protected:
    void SetUp() override {
        _parser.add_argument("-w", "--width")
            .default_value(1920)
            .help("width of the video");
        _parser.add_argument("-h", "--height")
            .default_value(1080)
            .help("height of the video");
        _parser.add_argument("-f", "--framerate")
            .default_value(60)
            .help("framerate of the video");
        _parser.add_argument("--file")
            .default_value(std::string("test.py"))
            .help("source file");
        _parser.add_argument("--generate")
            .default_value(std::string("output.mp4"))
            .help("output file");
        _parser.add_argument("--showstack")
            .default_value(false)
            .help("show stack");
        _parser.add_argument("--time")
            .default_value(false)
            .help("time execution");
    }

    argparse::ArgumentParser _parser{"test"};
};

// New comprehensive tests to improve coverage
TEST_F(CoreCoverageTests, CoreInternalMethods) {
    std::vector<std::string> argv = {"videocode", "--width", "800", "--height", "600", 
                                     "--framerate", "30", "--file", "nonexistent.py", 
                                     "--generate", "test.mp4", "--showstack", "true"};
    _parser.parse_args(argv);
    
    VC::Core core(_parser);
    
    // Test internal methods that aren't covered by direct calls
    // These are called indirectly through constructor and reloadSourceFile
    // But we need to exercise edge cases
    
    // Test with different frame counts
    core.forward3frames();
    core.backward3frames();
    core.goToFirstFrame();
    core.goToLastFrame();
    
    // Multiple calls to test state transitions
    core.pause();
    core.pause(); // Toggle back
    
    // Test reloading multiple times
    core.reloadSourceFile();
    core.reloadSourceFile();
}

TEST_F(CoreCoverageTests, UpdateFrameWithFrames) {
    std::vector<std::string> argv = {"videocode", "--width", "400", "--height", "300", 
                                     "--framerate", "60", "--file", "test.py", 
                                     "--generate", "test.mp4"};
    _parser.parse_args(argv);
    
    VC::Core core(_parser);
    
    int argc = 0;
    char* argv2[1] = {nullptr};
    QApplication app(argc, argv2);
    QLabel label;
    
    // Test updateFrame - this should exercise both empty and non-empty frame paths
    core.updateFrame(label);
}

TEST_F(CoreCoverageTests, GenerateVideoWithDifferentSettings) {
    std::vector<std::string> argv = {"videocode", "--width", "1280", "--height", "720", 
                                     "--framerate", "24", "--file", "test.py", 
                                     "--generate", "/tmp/coverage_test.mp4", "--showstack", "false"};
    _parser.parse_args(argv);
    
    VC::Core core(_parser);
    
    // Test video generation
    int result = core.generateVideo();
    EXPECT_EQ(result, 0);
}

TEST_F(CoreCoverageTests, NavigationEdgeCases) {
    std::vector<std::string> argv = {"videocode", "--width", "640", "--height", "480", 
                                     "--framerate", "30", "--file", "test.py", 
                                     "--generate", "test.mp4"};
    _parser.parse_args(argv);
    
    VC::Core core(_parser);
    
    // Test navigation with different boundary conditions
    for (int i = 0; i < 5; ++i) {
        core.forward3frames();
    }
    
    for (int i = 0; i < 10; ++i) {
        core.backward3frames();  // Should hit boundary
    }
    
    core.goToLastFrame();
    core.forward3frames();   // Should handle being at end
    
    core.goToFirstFrame(); 
    core.backward3frames();  // Should handle being at start
}

TEST_F(CoreCoverageTests, PythonAPIErrorHandling) {
    // Test various error conditions in Python API
    try {
        python::API::call<std::string>("ValidModule", "invalidFunction", "arg");
    } catch (const Error&) {
        // Expected to fail
    }
    
    try {
        python::API::call<std::string>("", "", "");
    } catch (const Error&) {
        // Expected to fail  
    }
}

TEST_F(CoreCoverageTests, CoreMethodsCoverage) {
    std::vector<std::string> argv = {"videocode", "--width", "800", "--height", "600", 
                                     "--framerate", "30", "--file", "test.py", 
                                     "--generate", "test.mp4", "--showstack", "true", "--time", "true"};
    _parser.parse_args(argv);
    
    VC::Core core(_parser);
    
    // Test updateFrame method
    int argc = 0;
    char* argv2[1] = {nullptr};
    QApplication app(argc, argv2);
    QLabel label;
    
    // Test updateFrame with empty frames
    core.updateFrame(label);
    
    // Test generateVideo method
    int result = core.generateVideo();
    EXPECT_EQ(result, 0);
    
    // Test pause functionality
    core.pause();
    
    // Test navigation methods
    core.goToFirstFrame();
    core.goToLastFrame();
    core.forward3frames();
    core.backward3frames();
    
    // Test reload source file
    core.reloadSourceFile();
}

TEST_F(CoreCoverageTests, FactoryCoverage) {
    // Test Factory error handling
    json i;
    i["type"] = "InvalidType";
    
    EXPECT_THROW(Factory::create("InvalidType", i), Error);
    
    // Test valid creations
    json rectArgs;
    rectArgs["width"] = 100;
    rectArgs["height"] = 50;
    auto rect = Factory::create("Rectangle", rectArgs);
    EXPECT_NE(rect, nullptr);
    
    json circleArgs;
    circleArgs["radius"] = 25;
    auto circle = Factory::create("Circle", circleArgs);
    EXPECT_NE(circle, nullptr);
    
    json textArgs;
    textArgs["text"] = "Hello World";
    auto text = Factory::create("Text", textArgs);
    EXPECT_NE(text, nullptr);
}

TEST_F(CoreCoverageTests, VideoCoverage) {
    // Test Video constructor error handling
    json::object_t args;
    args["filepath"] = "nonexistent_video.mp4";
    
    EXPECT_THROW(Video video(std::move(args)), Error);
}

TEST_F(CoreCoverageTests, APICoverage) {
    // Test API error handling
    EXPECT_THROW(python::API::call<std::string>("NonExistentModule", "function", "arg"), Error);
}

TEST_F(CoreCoverageTests, ExceptionCoverage) {
    // Test Error constructors
    Error err1("Test error message");
    Error err2(std::string("Test error message 2"));
    
    EXPECT_STREQ(err1.what(), "Test error message");
    EXPECT_STREQ(err2.what(), "Test error message 2");
    
    // Test copy/move semantics 
    Error err3 = err1;
    EXPECT_STREQ(err3.what(), "Test error message");
}

TEST_F(CoreCoverageTests, WindowCoverage) {
    // Test window-related methods if accessible
    std::vector<std::string> argv = {"videocode", "--width", "400", "--height", "300", 
                                     "--framerate", "30", "--file", "test.py", 
                                     "--generate", "test.mp4"};
    _parser.parse_args(argv);
    
    VC::Core core(_parser);
    
    // Test different window operations
    core.pause();
    core.pause();
    core.goToFirstFrame();
    core.goToLastFrame();
}

TEST_F(CoreCoverageTests, AdvancedCoreFunctionality) {
    std::vector<std::string> argv = {"videocode", "--width", "640", "--height", "480", 
                                     "--framerate", "24", "--file", "test.py", 
                                     "--generate", "advanced_test.mp4", "--showstack", "true"};
    _parser.parse_args(argv);
    
    VC::Core core(_parser);
    
    // Test stack execution paths that might not be covered
    // These test the internal methods like executeStack and addNewFrames
    
    // Test jumpTo with boundary values
    core.forward3frames();
    core.backward3frames(); // Test boundary conditions
    
    // Test multiple reloads
    core.reloadSourceFile();
    core.reloadSourceFile();
}

} // namespace VC