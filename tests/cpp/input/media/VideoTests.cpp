#include <gtest/gtest.h>
#include "input/media/Video.hpp"
#include "input/Frame.hpp"

class VideoTests : public ::testing::Test {
protected:
    void SetUp() override {
        validArgs = {
            {"filepath", "test_video.mp4"},
            {"start", 0.0},
            {"duration", 5.0}
        };
    }

    json::object_t validArgs;
};

TEST_F(VideoTests, ConstructorBasicValidation) {
    EXPECT_NO_THROW({
        json::object_t args = validArgs;
        Video video(std::move(args));
    });
}

TEST_F(VideoTests, ConstructorErrorHandling) {
    json::object_t args = validArgs;
    
    // Test missing path
    args.erase("path");
    EXPECT_THROW({
        Video video(std::move(args));
    }, std::exception);
    
    // Test negative duration
    args = validArgs;
    args["duration"] = -1.0;
    EXPECT_THROW({
        Video video(std::move(args));
    }, std::exception);
}

TEST_F(VideoTests, ArgsAccess) {
    json::object_t args = validArgs;
    Video video(std::move(args));
    const auto& actualArgs = video.getArgs();

    EXPECT_GT(actualArgs.at("width").get<int>(), 0);
    EXPECT_GT(actualArgs.at("height").get<int>(), 0);
    EXPECT_FLOAT_EQ(actualArgs.at("start").get<float>(), validArgs.at("start").get<float>());
    EXPECT_FLOAT_EQ(actualArgs.at("duration").get<float>(), validArgs.at("duration").get<float>());
}