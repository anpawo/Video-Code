#include <gtest/gtest.h>

#include <nlohmann/json.hpp>

#include "input/shape/Circle.hpp"

using json = nlohmann::json;

TEST(CircleTests, ConstructWithArgsProducesFrame)
{
    json j;
    j["radius"] = 50;
    j["thickness"] = 1;
    j["color"] = json::array({0, 0, 0, 255});
    j["filled"] = true;

    Circle circle(j.get<json::object_t>());

    Frame &frame = circle.getLastFrame();
    EXPECT_FALSE(frame.mat.empty());
    // Default metadata values
    EXPECT_EQ(frame.meta.position.x, 0);
    EXPECT_EQ(frame.meta.position.y, 0);
}
