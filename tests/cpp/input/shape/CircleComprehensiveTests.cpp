#include <gtest/gtest.h>
#include "input/shape/Circle.hpp"
#include "input/Frame.hpp"
#include <nlohmann/json.hpp>

class CircleComprehensiveTests : public ::testing::Test {
protected:
    void SetUp() override {
        basicArgs = {
            {"radius", 25},
            {"thickness", 1},
            {"filled", true},
            {"color", nlohmann::json::array({255, 128, 0, 255})}
        };
        
        largeArgs = {
            {"radius", 100},
            {"thickness", 3},
            {"filled", false},
            {"color", nlohmann::json::array({0, 255, 0, 200})}
        };
        
        smallArgs = {
            {"radius", 1},
            {"thickness", 1},
            {"filled", true},
            {"color", nlohmann::json::array({255, 255, 0, 255})}
        };
        
        zeroArgs = {
            {"radius", 0},
            {"thickness", 1},
            {"filled", true},
            {"color", nlohmann::json::array({255, 0, 0, 255})}
        };
    }
    
    nlohmann::json basicArgs;
    nlohmann::json largeArgs;
    nlohmann::json smallArgs;
    nlohmann::json zeroArgs;
};

TEST_F(CircleComprehensiveTests, BasicCircleConstruction) {
    Circle circle(basicArgs);
    
    Frame& frame = circle.generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
}

TEST_F(CircleComprehensiveTests, LargeCircleWithColor) {
    Circle circle(largeArgs);
    
    Frame& frame = circle.generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
    
    cv::Mat mat = frame.mat;
    // Should have 4 channels (BGRA)
    EXPECT_EQ(mat.channels(), 4);
}

TEST_F(CircleComprehensiveTests, SmallCircle) {
    Circle circle(smallArgs);
    
    Frame& frame = circle.generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
}

TEST_F(CircleComprehensiveTests, ZeroRadiusCircle) {
    try {
        Circle circle(zeroArgs);
        Frame& frame = circle.generateNextFrame();
        // Zero radius should still produce a frame (even if it's minimal)
        EXPECT_FALSE(frame.mat.empty());
    } catch (...) {
        // Exception is also acceptable for zero radius
        SUCCEED();
    }
}

TEST_F(CircleComprehensiveTests, MissingRadiusArgument) {
    nlohmann::json emptyArgs;
    
    EXPECT_THROW(Circle circle(emptyArgs), std::exception);
}

TEST_F(CircleComprehensiveTests, MultipleFrameGeneration) {
    Circle circle(basicArgs);
    
    // Generate multiple frames
    for (int i = 0; i < 3; ++i) {
        Frame& frame = circle.generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}

TEST_F(CircleComprehensiveTests, DifferentColorConfigurations) {
    nlohmann::json redCircle = {
        {"radius", 30},
        {"color", nlohmann::json::array({255, 0, 0, 255})}
    };
    
    nlohmann::json transparentCircle = {
        {"radius", 50},
        {"color", nlohmann::json::array({128, 128, 128, 50})}
    };
    
    Circle red(redCircle);
    Circle transparent(transparentCircle);
    
    EXPECT_FALSE(red.generateNextFrame().mat.empty());
    EXPECT_FALSE(transparent.generateNextFrame().mat.empty());
}