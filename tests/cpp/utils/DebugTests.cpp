#include <gtest/gtest.h>

// Tests with debug enabled
#define VC_DEBUG_ON
#include <iostream>
#include <sstream>

#include "utils/Debug.hpp"

class DebugTests : public ::testing::Test
{
protected:

    void SetUp() override
    {
        oldBuf = std::cout.rdbuf(oss.rdbuf());
    }

    void TearDown() override
    {
        std::cout.rdbuf(oldBuf);
    }

    std::ostringstream oss;
    std::streambuf* oldBuf;
};

TEST_F(DebugTests, PrintsWhenEnabled)
{
    VC_LOG_DEBUG("test-debug-message");
    std::string out = oss.str();
    EXPECT_NE(out.find("test-debug-message"), std::string::npos);
}

TEST_F(DebugTests, HandlesMultipleMessages)
{
    VC_LOG_DEBUG("message1");
    VC_LOG_DEBUG("message2");

    std::string out = oss.str();
    EXPECT_NE(out.find("message1"), std::string::npos);
    EXPECT_NE(out.find("message2"), std::string::npos);
}

TEST_F(DebugTests, HandlesEmptyMessage)
{
    VC_LOG_DEBUG("");
    std::string out = oss.str();
    EXPECT_TRUE(out.length() > 0); // Should still print newline
}
