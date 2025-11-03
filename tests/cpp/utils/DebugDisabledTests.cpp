#include <gtest/gtest.h>

// Include Debug.hpp without defining VC_DEBUG_ON to test disabled behavior
#include "utils/Debug.hpp"

#include <iostream>
#include <sstream>

class DebugDisabledTests : public ::testing::Test {
protected:
    void SetUp() override {
        oldBuf = std::cout.rdbuf(oss.rdbuf());
    }
    
    void TearDown() override {
        std::cout.rdbuf(oldBuf);
    }
    
    std::ostringstream oss;
    std::streambuf* oldBuf;
};

TEST_F(DebugDisabledTests, SilentWhenDisabled) {
    VC_LOG_DEBUG("should-not-appear");
    std::string out = oss.str();
    EXPECT_EQ(out.find("should-not-appear"), std::string::npos);
}
