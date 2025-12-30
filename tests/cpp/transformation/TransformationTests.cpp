#include <gtest/gtest.h>

#include "transformation/transformation.hpp"

using namespace transformation;

TEST(TransformationMap, ContainsKnownTransformations)
{
    // Ensure the transformation map contains the expected keys declared in the header
    EXPECT_NE(map.find("fade"), map.end());
    EXPECT_NE(map.find("grayscale"), map.end());
    EXPECT_NE(map.find("moveTo"), map.end());
    EXPECT_NE(map.find("zoom"), map.end());
    EXPECT_NE(map.find("scale"), map.end());
    EXPECT_NE(map.find("setPosition"), map.end());
    EXPECT_NE(map.find("setArgument"), map.end());
}
