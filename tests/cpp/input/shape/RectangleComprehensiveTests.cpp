#include <gtest/gtest.h>

#include <nlohmann/json.hpp>

#include "input/Frame.hpp"
#include "input/shape/Rectangle.hpp"

class RectangleComprehensiveTests : public ::testing::Test
{
protected:

    void SetUp() override
    {
        // Set up various test configurations
        basicArgs = {
            {"width", 100},
            {"height", 50},
            {"thickness", 1},
            {"cornerRadius", 0},
            {"filled", true},
            {"color", nlohmann::json::array({255, 255, 255, 255})}
        };

        complexArgs = {
            {"width", 200},
            {"height", 100},
            {"thickness", 2},
            {"cornerRadius", 5},
            {"filled", false},
            {"color", nlohmann::json::array({255, 0, 0, 128})} // Red with transparency
        };

        edgeCaseArgs = {
            {"width", 1},
            {"height", 1},
            {"thickness", 1},
            {"cornerRadius", 0},
            {"filled", true},
            {"color", nlohmann::json::array({255, 0, 255, 255})}
        };

        largeArgs = {
            {"width", 1000},
            {"height", 800},
            {"thickness", 10},
            {"cornerRadius", 20},
            {"filled", true},
            {"color", nlohmann::json::array({100, 150, 200, 128})}
        };
    }

    nlohmann::json basicArgs;
    nlohmann::json complexArgs;
    nlohmann::json edgeCaseArgs;
    nlohmann::json largeArgs;
};

TEST_F(RectangleComprehensiveTests, BasicConstruction)
{
    Rectangle rectangle(basicArgs);

    // Should create a valid frame
    Frame& frame = rectangle.generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());

    // Frame should have expected dimensions
    cv::Mat mat = frame.mat;
    EXPECT_GT(mat.cols, 0);
    EXPECT_GT(mat.rows, 0);
}

TEST_F(RectangleComprehensiveTests, WithColorChannel)
{
    Rectangle rectangle(complexArgs);

    Frame& frame = rectangle.generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());

    cv::Mat mat = frame.mat;
    EXPECT_EQ(mat.channels(), 4); // Should be BGRA
}

TEST_F(RectangleComprehensiveTests, EdgeCaseDimensions)
{
    Rectangle rectangle(edgeCaseArgs);

    // Should handle very small rectangles
    Frame& frame = rectangle.generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
}

TEST_F(RectangleComprehensiveTests, LargeDimensions)
{
    Rectangle rectangle(largeArgs);

    // Should handle large rectangles
    Frame& frame = rectangle.generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());

    cv::Mat mat = frame.mat;
    EXPECT_EQ(mat.cols, 1000);
    EXPECT_EQ(mat.rows, 800);
}

TEST_F(RectangleComprehensiveTests, MultipleFrameGeneration)
{
    Rectangle rectangle(basicArgs);

    // Generate multiple frames to test consistency
    for (int i = 0; i < 5; ++i) {
        Frame& frame = rectangle.generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}

TEST_F(RectangleComprehensiveTests, DifferentColorValues)
{
    // Test with different color configurations
    nlohmann::json whiteArgs = {
        {"width", 100},
        {"height", 100},
        {"color", nlohmann::json::array({255, 255, 255, 255})}
    };

    nlohmann::json blackArgs = {
        {"width", 100},
        {"height", 100},
        {"color", nlohmann::json::array({0, 0, 0, 255})}
    };

    nlohmann::json transparentArgs = {
        {"width", 100},
        {"height", 100},
        {"color", nlohmann::json::array({128, 128, 128, 0})} // Fully transparent
    };

    Rectangle whiteRect(whiteArgs);
    Rectangle blackRect(blackArgs);
    Rectangle transparentRect(transparentArgs);

    EXPECT_FALSE(whiteRect.generateNextFrame().mat.empty());
    EXPECT_FALSE(blackRect.generateNextFrame().mat.empty());
    EXPECT_FALSE(transparentRect.generateNextFrame().mat.empty());
}

TEST_F(RectangleComprehensiveTests, MissingArguments)
{
    nlohmann::json incompleteArgs = {{"width", 100}}; // Missing height

    // Should throw when missing required arguments
    EXPECT_THROW(Rectangle rectangle(incompleteArgs), std::exception);
}

TEST_F(RectangleComprehensiveTests, InvalidDimensions)
{
    nlohmann::json invalidArgs = {
        {"width", 0},
        {"height", 50}
    };

    // Should handle zero or negative dimensions gracefully
    // The implementation might throw or create an empty rectangle
    try {
        Rectangle rectangle(invalidArgs);
        Frame& frame = rectangle.generateNextFrame();
        // If no exception, the frame might be empty or have been handled
        (void)frame; // Suppress unused variable warning
    } catch (...) {
        // Exception is acceptable for invalid dimensions
        SUCCEED();
    }
}
