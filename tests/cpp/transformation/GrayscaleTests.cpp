#include <gtest/gtest.h>

#include <memory>

#include "input/Frame.hpp"
#include "input/shape/Rectangle.hpp"
#include "transformation/transformation.hpp"

class GrayscaleTests : public ::testing::Test
{
protected:

    void SetUp() override
    {
        json::object_t rectArgs = {
            {"width", 100},
            {"height", 100},
            {"thickness", 2},
            {"cornerRadius", 0},
            {"filled", true},
            {"color", json::array_t{255, 128, 64, 255}}
        };
        input = std::make_shared<Rectangle>(std::move(rectArgs));
    }

    std::shared_ptr<IInput> input;
};

TEST_F(GrayscaleTests, ApplyGrayscale)
{
    json::object_t args = {
        {"duration", 5},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::grayscale(input, args));

    // Generate frames to execute the transformation
    for (int i = 0; i < 5; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());

        // Verify grayscale was applied (R=G=B for grayscale)
        if (frame.mat.rows > 0 && frame.mat.cols > 0) {
            cv::Vec4b pixel = frame.mat.at<cv::Vec4b>(frame.mat.rows / 2, frame.mat.cols / 2);
            EXPECT_EQ(pixel[0], pixel[1]);
            EXPECT_EQ(pixel[1], pixel[2]);
        }
    }
}

TEST_F(GrayscaleTests, GrayscaleWithLongerDuration)
{
    json::object_t args = {
        {"duration", 10},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::grayscale(input, args));

    for (int i = 0; i < 10; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}
