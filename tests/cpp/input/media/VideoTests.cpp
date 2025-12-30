#include <gtest/gtest.h>

#include <opencv2/videoio.hpp>

#include "input/Frame.hpp"
#include "input/media/Video.hpp"

class VideoTests : public ::testing::Test
{
protected:

    void SetUp() override
    {
        // Resolve resource path relative to this test file so tests work from any CWD
        std::string base = __FILE__;
        auto pos = base.find("/tests/cpp/");
        std::string resourcesPath = "tests/resources/test_video.mp4";
        if (pos != std::string::npos) {
            std::string projectRoot = base.substr(0, pos + 1);
            resourcesPath = projectRoot + std::string("tests/resources/test_video.mp4");
        }

        validArgs = {
            {"filepath", resourcesPath},
            {"start", 0.0},
            {"duration", 5.0}
        };
    }

    json::object_t validArgs;
};

TEST_F(VideoTests, ConstructorBasicValidation)
{
    // Skip if OpenCV cannot open the video file (e.g. ffmpeg backend missing)
    std::string path = validArgs.at("filepath").get<std::string>();
    cv::VideoCapture cap(path);
    if (!cap.isOpened()) {
        GTEST_SKIP() << "Cannot open video file with OpenCV (backend missing) - skipping test";
    }

    EXPECT_NO_THROW({
        json::object_t args = validArgs;
        Video video(std::move(args));
    });
}

TEST_F(VideoTests, ConstructorErrorHandling)
{
    json::object_t args = validArgs;

    // Test missing filepath
    args.erase("filepath");
    EXPECT_THROW({ Video video(std::move(args)); }, std::exception);

    // Test negative duration
    args = validArgs;
    args["duration"] = -1.0;
    EXPECT_THROW({ Video video(std::move(args)); }, std::exception);
}

TEST_F(VideoTests, ArgsAccess)
{
    // Skip if OpenCV cannot open the video file (e.g. ffmpeg backend missing)
    std::string path = validArgs.at("filepath").get<std::string>();
    cv::VideoCapture cap(path);
    if (!cap.isOpened()) {
        GTEST_SKIP() << "Cannot open video file with OpenCV (backend missing) - skipping test";
    }

    json::object_t args = validArgs;
    Video video(std::move(args));
    const auto& actualArgs = video.getArgs();

    EXPECT_GT(actualArgs.at("width").get<int>(), 0);
    EXPECT_GT(actualArgs.at("height").get<int>(), 0);
    EXPECT_FLOAT_EQ(actualArgs.at("start").get<float>(), validArgs.at("start").get<float>());
    EXPECT_FLOAT_EQ(actualArgs.at("duration").get<float>(), validArgs.at("duration").get<float>());
}
