#include <gtest/gtest.h>

#include <nlohmann/json.hpp>

#include "input/text/Text.hpp"

using json = nlohmann::json;

TEST(TextTests, ConstructWithArgsProducesFrame)
{
    json j;
    j["text"] = "Hello";
    j["fontSize"] = 1.0;
    j["fontThickness"] = 1;
    j["color"] = json::array({0, 0, 0, 255});

    Text text(j.get<json::object_t>());
    Frame &frame = text.getLastFrame();
    EXPECT_FALSE(frame.mat.empty());
    EXPECT_EQ(frame.meta.position.x, 0);
    EXPECT_EQ(frame.meta.position.y, 0);
}
