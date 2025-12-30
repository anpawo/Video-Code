#include <gtest/gtest.h>

#include <memory>

#include "input/Frame.hpp"
#include "input/media/Image.hpp"
#include "transformation/transformation.hpp"

class ColorTransformationTests : public ::testing::Test
{
protected:

    void SetUp() override
    {
        // Create a test image input
        input = std::make_shared<Image>(json::object());
    }

    std::shared_ptr<IInput> input;
};

TEST_F(ColorTransformationTests, FadeTransformation)
{
    json::object_t args = {
        {"start", 0},
        {"end", 1.0},
        {"duration", 2.0}
    };

    // Test fade transformation
    ASSERT_NO_THROW(transformation::fade(input, args));

    // Test invalid args
    json::object_t invalid_args = {{"start", "invalid"}};
    ASSERT_THROW(transformation::fade(input, invalid_args), std::exception);
}

TEST_F(ColorTransformationTests, GrayscaleTransformation)
{
    json::object_t args = {
        {"intensity", 1.0}
    };

    // Test grayscale transformation
    ASSERT_NO_THROW(transformation::grayscale(input, args));

    // Test invalid args
    json::object_t invalid_args = {{"intensity", "invalid"}};
    ASSERT_THROW(transformation::grayscale(input, invalid_args), std::exception);
}
