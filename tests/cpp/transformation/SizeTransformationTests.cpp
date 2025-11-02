#include <gtest/gtest.h>
#include <memory>
#include "transformation/transformation.hpp"
#include "input/Frame.hpp"
#include "input/media/Image.hpp"

class SizeTransformationTests : public ::testing::Test {
protected:
    void SetUp() override {
        // Create a test image input
        input = std::make_shared<Image>(json::object());
    }

    std::shared_ptr<IInput> input;
};

TEST_F(SizeTransformationTests, ZoomTransformation) {
    json::object_t args = {
        {"scale", 2.0},
        {"duration", 1.0}
    };
    
    // Test zoom transformation
    ASSERT_NO_THROW(transformation::zoom(input, args));
    
    // Test with invalid scale
    json::object_t invalid_scale = {
        {"scale", 0.0},
        {"duration", 1.0}
    };
    ASSERT_THROW(transformation::zoom(input, invalid_scale), std::exception);
}

TEST_F(SizeTransformationTests, ScaleTransformation) {
    json::object_t args = {
        {"x", 2.0},
        {"y", 2.0}
    };
    
    // Test scale transformation
    ASSERT_NO_THROW(transformation::scale(input, args));
    
    // Test with negative scale
    json::object_t negative_scale = {
        {"x", -1.0},
        {"y", 1.0}
    };
    ASSERT_THROW(transformation::scale(input, negative_scale), std::exception);
}