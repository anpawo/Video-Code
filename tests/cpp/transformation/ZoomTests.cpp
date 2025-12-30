#include <gtest/gtest.h>

#include <memory>

#include "input/Frame.hpp"
#include "input/shape/Rectangle.hpp"
#include "transformation/transformation.hpp"

class ZoomTests : public ::testing::Test
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
            {"color", json::array_t{255, 255, 0, 255}}
        };
        input = std::make_shared<Rectangle>(std::move(rectArgs));
    }

    std::shared_ptr<IInput> input;
};

TEST_F(ZoomTests, ZoomWithIntegerCoordinates)
{
    json::object_t args = {
        {"x", 50},
        {"y", 50},
        {"factor", json::array_t{1.0, 2.0}},
        {"duration", 5},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::zoom(input, args));

    for (int i = 0; i < 5; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}

TEST_F(ZoomTests, ZoomWithFloatCoordinates)
{
    json::object_t args = {
        {"x", 0.5},
        {"y", 0.5},
        {"factor", json::array_t{0.5, 1.5}},
        {"duration", 8},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::zoom(input, args));

    for (int i = 0; i < 8; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}

TEST_F(ZoomTests, ZoomOut)
{
    json::object_t args = {
        {"x", 0.25},
        {"y", 0.75},
        {"factor", json::array_t{2.0, 0.5}},
        {"duration", 10},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::zoom(input, args));

    for (int i = 0; i < 10; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}
