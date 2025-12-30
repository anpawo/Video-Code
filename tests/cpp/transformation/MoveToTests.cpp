#include <gtest/gtest.h>

#include <memory>

#include "input/Frame.hpp"
#include "input/shape/Circle.hpp"
#include "transformation/transformation.hpp"

class MoveToTests : public ::testing::Test
{
protected:

    void SetUp() override
    {
        json::object_t circleArgs = {
            {"radius", 25},
            {"thickness", 1},
            {"filled", true},
            {"color", json::array_t{0, 255, 0, 255}}
        };
        input = std::make_shared<Circle>(std::move(circleArgs));
    }

    std::shared_ptr<IInput> input;
};

TEST_F(MoveToTests, MoveFromOriginToDest)
{
    json::object_t args = {
        {"srcX", 0},
        {"srcY", 0},
        {"dstX", 100},
        {"dstY", 100},
        {"duration", 10},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::moveTo(input, args));

    for (int i = 0; i < 10; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}

TEST_F(MoveToTests, MoveWithNullDstX)
{
    json::object_t args = {
        {"srcX", 50},
        {"srcY", 50},
        {"dstX", nullptr},
        {"dstY", 150},
        {"duration", 5},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::moveTo(input, args));

    for (int i = 0; i < 5; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}

TEST_F(MoveToTests, MoveWithNullDstY)
{
    json::object_t args = {
        {"srcX", 20},
        {"srcY", 30},
        {"dstX", 120},
        {"dstY", nullptr},
        {"duration", 8},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::moveTo(input, args));

    for (int i = 0; i < 8; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}

TEST_F(MoveToTests, MoveWithZeroDuration)
{
    json::object_t args = {
        {"srcX", 0},
        {"srcY", 0},
        {"dstX", 100},
        {"dstY", 100},
        {"duration", 0},
        {"start", 0}
    };

    // Should return early for zero duration
    EXPECT_NO_THROW(transformation::moveTo(input, args));
}

TEST_F(MoveToTests, MoveWithBothDstNull)
{
    json::object_t args = {
        {"srcX", 10},
        {"srcY", 10},
        {"dstX", nullptr},
        {"dstY", nullptr},
        {"duration", 3},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::moveTo(input, args));

    for (int i = 0; i < 3; i++) {
        auto& frame = input->generateNextFrame();
        EXPECT_FALSE(frame.mat.empty());
    }
}
