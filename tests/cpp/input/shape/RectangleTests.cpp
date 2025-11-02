#include <gtest/gtest.h>
#include <nlohmann/json.hpp>
#include "input/shape/Rectangle.hpp"

using json = nlohmann::json;

TEST(RectangleTests, ConstructWithArgsProducesFrame) {
    json j;
    j["width"] = 100;
    j["height"] = 50;
    j["thickness"] = 1;
    j["color"] = json::array({0, 0, 0, 255});
    j["cornerRadius"] = 0;
    j["filled"] = true;

    Rectangle rect(j.get<json::object_t>());
    Frame &frame = rect.getLastFrame();
    EXPECT_FALSE(frame.mat.empty());
    EXPECT_EQ(frame.meta.position.x, 0);
    EXPECT_EQ(frame.meta.position.y, 0);
}