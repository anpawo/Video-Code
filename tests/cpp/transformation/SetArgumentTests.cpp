#include <gtest/gtest.h>
#include "transformation/transformation.hpp"
#include "input/shape/Circle.hpp"
#include "input/Frame.hpp"
#include <memory>

class SetArgumentTests : public ::testing::Test {
protected:
    void SetUp() override {
        json::object_t circleArgs = {
            {"radius", 30},
            {"thickness", 1},
            {"filled", true},
            {"color", json::array_t{200, 100, 50, 255}}
        };
        input = std::make_shared<Circle>(std::move(circleArgs));
    }

    std::shared_ptr<IInput> input;
};

TEST_F(SetArgumentTests, SetIntegerArgument) {
    json::object_t args = {
        {"name", "radius"},
        {"value", 50},
        {"start", 0}
    };
    
    EXPECT_NO_THROW(transformation::setArgument(input, args));
    
    // Flush transformation to trigger setter
    input->flushTransformation();
    auto& frame = input->generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
    
    // Verify argument was updated
    const auto& inputArgs = input->getArgs();
    EXPECT_EQ(inputArgs.at("radius").get<int>(), 50);
}

TEST_F(SetArgumentTests, SetStringArgument) {
    json::object_t args = {
        {"name", "test_string"},
        {"value", "hello"},
        {"start", 0}
    };
    
    EXPECT_NO_THROW(transformation::setArgument(input, args));
    
    input->flushTransformation();
    auto& frame = input->generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
}

TEST_F(SetArgumentTests, SetFloatArgument) {
    json::object_t args = {
        {"name", "opacity"},
        {"value", 0.75},
        {"start", 0}
    };
    
    EXPECT_NO_THROW(transformation::setArgument(input, args));
    
    input->flushTransformation();
    auto& frame = input->generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
}
