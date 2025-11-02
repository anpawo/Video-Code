#include <gtest/gtest.h>
#include <memory>
#include "transformation/transformation.hpp"
#include "input/Frame.hpp"
#include "input/media/Image.hpp"

class PositionTransformationTests : public ::testing::Test {
protected:
    void SetUp() override {
        // Create a test image input
        input = std::make_shared<Image>(json::object());
    }

    std::shared_ptr<IInput> input;
};

TEST_F(PositionTransformationTests, MoveToTransformation) {
    json::object_t args = {
        {"x", 100},
        {"y", 200},
        {"duration", 2.0}
    };
    
    // Test moveTo transformation
    ASSERT_NO_THROW(transformation::moveTo(input, args));
    
    // Test with missing coordinates
    json::object_t missing_coords = {{"duration", 1.0}};
    ASSERT_THROW(transformation::moveTo(input, missing_coords), std::exception);
    
    // Test with invalid duration
    json::object_t invalid_duration = {
        {"x", 100},
        {"y", 200},
        {"duration", -1.0}
    };
    ASSERT_THROW(transformation::moveTo(input, invalid_duration), std::exception);
}