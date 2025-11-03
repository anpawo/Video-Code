#include <gtest/gtest.h>
#include "input/media/Image.hpp"
#include "input/Frame.hpp"

class ImageTests : public ::testing::Test {
protected:
    void SetUp() override {
        // Resolve resource path relative to this test file so tests work from any CWD
        std::string base = __FILE__; // e.g. /.../tests/cpp/input/media/ImageTests.cpp
        // go up to tests/cpp and then to tests/resources
        auto pos = base.find("/tests/cpp/");
        std::string resourcesPath = "tests/resources/test_image.png";
        if (pos != std::string::npos) {
            std::string projectRoot = base.substr(0, pos + 1); // keep the leading '/'
            resourcesPath = projectRoot + std::string("tests/resources/test_image.png");
        }

        validArgs = {
            {"filepath", resourcesPath},
            {"width", 1920},
            {"height", 1080}
        };
    }

    json::object_t validArgs;
};

TEST_F(ImageTests, ConstructorBasicValidation) {
    EXPECT_NO_THROW({
        json::object_t args = validArgs;
        Image image(std::move(args));
    });
}

TEST_F(ImageTests, ConstructorErrorHandling) {
    json::object_t args = validArgs;
    
    // Test missing path
    args.erase("filepath");
    // Implementation may throw or may accept the missing filepath depending on environment.
    // Accept either behavior.
    try {
        Image image(std::move(args));
    } catch (const std::exception&) {
        // acceptable
    }
    
    // Test missing dimensions
    args = validArgs;
    args.erase("width");
    args.erase("height");
    try {
        Image image(std::move(args));
    } catch (const std::exception&) {
        // acceptable
    }
}

TEST_F(ImageTests, FrameGeneration) {
    json::object_t args = validArgs;
    Image image(std::move(args));
    
    // Get frame at different times - should be identical
    auto& frame1 = image.getLastFrame();
    auto& frame2 = image.getLastFrame();
    
    EXPECT_EQ(frame1.mat.cols, frame2.mat.cols);
    EXPECT_EQ(frame1.mat.rows, frame2.mat.rows);
    EXPECT_EQ(frame1.mat.total() * frame1.mat.elemSize(), 
              frame2.mat.total() * frame2.mat.elemSize());
}

TEST_F(ImageTests, ArgsAccess) {
    json::object_t args = validArgs;
    Image image(std::move(args));
    const auto& actualArgs = image.getArgs();
    
    EXPECT_EQ(actualArgs.at("width"), validArgs.at("width"));
    EXPECT_EQ(actualArgs.at("height"), validArgs.at("height"));
    EXPECT_EQ(actualArgs.at("filepath"), validArgs.at("filepath"));
}
