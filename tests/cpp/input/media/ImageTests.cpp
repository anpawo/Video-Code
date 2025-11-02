#include <gtest/gtest.h>
#include "input/media/Image.hpp"
#include "input/Frame.hpp"

class ImageTests : public ::testing::Test {
protected:
    void SetUp() override {
        validArgs = {
            {"path", "test_image.png"},
            {"width", 1920},
            {"height", 1080}
        };
    }

    json::object_t validArgs;
};

TEST_F(ImageTests, ConstructorBasicValidation) {
    EXPECT_NO_THROW({
        Image image(validArgs);
    });
}

TEST_F(ImageTests, ConstructorErrorHandling) {
    json::object_t args = validArgs;
    
    // Test missing path
    args.erase("path");
    EXPECT_THROW({
        Image image(args);
    }, std::exception);
    
    // Test missing dimensions
    args = validArgs;
    args.erase("width");
    args.erase("height");
    EXPECT_THROW({
        Image image(args);
    }, std::exception);
}

TEST_F(ImageTests, FrameGeneration) {
    Image image(validArgs);
    
    // Get frame at different times - should be identical
    auto frame1 = image.frame_at(0.0);
    auto frame2 = image.frame_at(1.0);
    
    EXPECT_EQ(frame1.metadata.width, frame2.metadata.width);
    EXPECT_EQ(frame1.metadata.height, frame2.metadata.height);
    EXPECT_EQ(frame1.data.size(), frame2.data.size());
}

TEST_F(ImageTests, MetadataAccess) {
    Image image(validArgs);
    const auto& meta = image.metadata();
    
    EXPECT_EQ(meta.width, validArgs["width"]);
    EXPECT_EQ(meta.height, validArgs["height"]);
    EXPECT_GE(meta.duration, 0);
    EXPECT_EQ(meta.start, 0);
}
