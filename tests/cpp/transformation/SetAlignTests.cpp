#include <gtest/gtest.h>

#include <memory>

#include "input/Frame.hpp"
#include "input/shape/Rectangle.hpp"
#include "transformation/transformation.hpp"

class SetAlignTests : public ::testing::Test
{
protected:

    void SetUp() override
    {
        json::object_t rectArgs = {
            {"width", 80},
            {"height", 80},
            {"thickness", 2},
            {"cornerRadius", 0},
            {"filled", true},
            {"color", json::array_t{128, 128, 128, 255}}
        };
        input = std::make_shared<Rectangle>(std::move(rectArgs));
    }

    std::shared_ptr<IInput> input;
};

TEST_F(SetAlignTests, SetAlignCenter)
{
    json::object_t args = {
        {"x", "center"},
        {"y", "center"},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::setAlign(input, args));

    auto& frame = input->generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
    EXPECT_FLOAT_EQ(frame.meta.align.x, -0.5f);
    EXPECT_FLOAT_EQ(frame.meta.align.y, -0.5f);
}

TEST_F(SetAlignTests, SetAlignLeft)
{
    json::object_t args = {
        {"x", "left"},
        {"y", nullptr},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::setAlign(input, args));

    auto& frame = input->generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
    EXPECT_FLOAT_EQ(frame.meta.align.x, -1.0f); // left is -1 in alignRatio
}

TEST_F(SetAlignTests, SetAlignRight)
{
    json::object_t args = {
        {"x", "right"},
        {"y", nullptr},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::setAlign(input, args));

    auto& frame = input->generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
    EXPECT_FLOAT_EQ(frame.meta.align.x, 0.0f); // right is 0 in alignRatio
}

TEST_F(SetAlignTests, SetAlignTop)
{
    json::object_t args = {
        {"x", nullptr},
        {"y", "top"},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::setAlign(input, args));

    auto& frame = input->generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
    EXPECT_FLOAT_EQ(frame.meta.align.y, -1.0f); // top is -1 in alignRatio
}

TEST_F(SetAlignTests, SetAlignBottom)
{
    json::object_t args = {
        {"x", nullptr},
        {"y", "bottom"},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::setAlign(input, args));

    auto& frame = input->generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
    EXPECT_FLOAT_EQ(frame.meta.align.y, 0.0f); // bottom is 0 in alignRatio
}

TEST_F(SetAlignTests, SetAlignBothNull)
{
    json::object_t args = {
        {"x", nullptr},
        {"y", nullptr},
        {"start", 0}
    };

    EXPECT_NO_THROW(transformation::setAlign(input, args));

    auto& frame = input->generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
}
