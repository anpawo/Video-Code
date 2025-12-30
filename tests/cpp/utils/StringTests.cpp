#include <gtest/gtest.h>

#include <string>

#include "utils/String.hpp"

TEST(StringTests, PlusOperatorWithInt)
{
    std::string base = "value";
    std::string res = base + 42;
    EXPECT_EQ(res, std::string("value42"));
}

TEST(StringTests, IntPlusOperatorWithString)
{
    std::string res = 7 + std::string("units");
    EXPECT_EQ(res, std::string("7units"));
}
