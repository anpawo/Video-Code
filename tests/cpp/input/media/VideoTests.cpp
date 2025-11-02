#include <gtest/gtest.h>
#include "input/media/Video.hpp"
#include "input/Frame.hpp"

class VideoTests : public ::testing::Test {
protected:
    void SetUp() override {
        validArgs = {
            {"path", "test_video.mp4"},
            {"start", 0.0},
            {"duration", 5.0}
        };
    }

    json::object_t validArgs;
};

TEST_F(VideoTests, ConstructorBasicValidation) {
    EXPECT_NO_THROW({
        Video video(validArgs);
    });
}

TEST_F(VideoTests, ConstructorErrorHandling) {
    json::object_t args = validArgs;
    
    // Test missing path
    args.erase("path");
    EXPECT_THROW({
        Video video(args);
    }, std::exception);
    
    // Test negative duration
    args = validArgs;
    args["duration"] = -1.0;
    EXPECT_THROW({
        Video video(args);
    }, std::exception);
}

TEST_F(VideoTests, MetadataAccess) {
    Video video(validArgs);
    const auto& meta = video.metadata();
    
    EXPECT_GE(meta.width, 0);
    EXPECT_GE(meta.height, 0);
    EXPECT_EQ(meta.start, validArgs["start"]);
    EXPECT_EQ(meta.duration, validArgs["duration"]);
}