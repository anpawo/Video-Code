#include <gtest/gtest.h>
#include "transformation/transformation.hpp"
#include "input/shape/Circle.hpp"
#include "input/Frame.hpp"
#include <memory>

class ScaleTests : public ::testing::Test {
protected:
    void SetUp() override {
        json::object_t circleArgs = {
            {"radius", 40},
            {"thickness", 1},
            {"filled", true},
            {"color", json::array_t{0, 255, 255, 255}}
        };
        input = std::make_shared<Circle>(std::move(circleArgs));
    }

    std::shared_ptr<IInput> input;
};

TEST_F(ScaleTests, ScaleUp) {
    json::object_t args = {
        {"factor", json::array_t{1.0, 2.0}},
        {"duration", 6},
        {"start", 0}
    };
    
    EXPECT_NO_THROW(transformation::scale(input, args));
    
    for (int i = 0; i < 6; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}

TEST_F(ScaleTests, ScaleDown) {
    json::object_t args = {
        {"factor", json::array_t{2.0, 0.5}},
        {"duration", 10},
        {"start", 0}
    };
    
    EXPECT_NO_THROW(transformation::scale(input, args));
    
    for (int i = 0; i < 10; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}

TEST_F(ScaleTests, ScaleSmallDuration) {
    json::object_t args = {
        {"factor", json::array_t{0.8, 1.2}},
        {"duration", 2},
        {"start", 0}
    };
    
    EXPECT_NO_THROW(transformation::scale(input, args));
    
    for (int i = 0; i < 2; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}
