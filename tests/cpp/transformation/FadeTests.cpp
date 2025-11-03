#include <gtest/gtest.h>
#include "transformation/transformation.hpp"
#include "input/shape/Circle.hpp"
#include "input/Frame.hpp"
#include <memory>

class FadeTests : public ::testing::Test {
protected:
    void SetUp() override {
        // Create a simple circle input
        json::object_t circleArgs = {
            {"radius", 50},
            {"thickness", 1},
            {"filled", true},
            {"color", json::array_t{255, 0, 0, 255}}
        };
        input = std::make_shared<Circle>(std::move(circleArgs));
    }

    std::shared_ptr<IInput> input;
};

TEST_F(FadeTests, FadeFromLeft) {
    json::object_t args = {
        {"sides", json::array_t{"left"}},
        {"affectTransparentPixel", false},
        {"startOpacity", 255.0f},
        {"endOpacity", 0.0f},
        {"duration", 5},
        {"start", 0}
    };
    
    EXPECT_NO_THROW(transformation::fade(input, args));
    
    // Generate frames to execute the transformation
    for (int i = 0; i < 5; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}

TEST_F(FadeTests, FadeFromRight) {
    json::object_t args = {
        {"sides", json::array_t{"right"}},
        {"affectTransparentPixel", true},
        {"startOpacity", 0.0f},
        {"endOpacity", 255.0f},
        {"duration", 3},
        {"start", 0}
    };
    
    EXPECT_NO_THROW(transformation::fade(input, args));
    
    for (int i = 0; i < 3; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}

TEST_F(FadeTests, FadeFromTop) {
    json::object_t args = {
        {"sides", json::array_t{"top"}},
        {"affectTransparentPixel", false},
        {"startOpacity", 128.0f},
        {"endOpacity", 255.0f},
        {"duration", 4},
        {"start", 0}
    };
    
    EXPECT_NO_THROW(transformation::fade(input, args));
    
    for (int i = 0; i < 4; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}

TEST_F(FadeTests, FadeFromBottom) {
    json::object_t args = {
        {"sides", json::array_t{"bottom"}},
        {"affectTransparentPixel", false},
        {"startOpacity", 255.0f},
        {"endOpacity", 128.0f},
        {"duration", 2},
        {"start", 0}
    };
    
    EXPECT_NO_THROW(transformation::fade(input, args));
    
    for (int i = 0; i < 2; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}

TEST_F(FadeTests, FadeMultipleSides) {
    json::object_t args = {
        {"sides", json::array_t{"left", "top"}},
        {"affectTransparentPixel", false},
        {"startOpacity", 255.0f},
        {"endOpacity", 0.0f},
        {"duration", 3},
        {"start", 0}
    };
    
    EXPECT_NO_THROW(transformation::fade(input, args));
    
    for (int i = 0; i < 3; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}
