#include <gtest/gtest.h>
#include "utils/Map.hpp"
#include <sstream>
#include <map>

class MapTests : public ::testing::Test {
protected:
    void SetUp() override {
        // Initialize test maps
        stringIntMap = {{"alpha", 1}, {"beta", 2}, {"gamma", 3}};
        stringStringMap = {{"key1", "value1"}, {"key2", "value2"}};
        intDoubleMap = {{1, 1.5}, {2, 2.5}};
    }

    std::map<std::string, int> stringIntMap;
    std::map<std::string, std::string> stringStringMap;
    std::map<int, double> intDoubleMap;
};

TEST_F(MapTests, StringIntMapStream) {
    std::ostringstream oss;
    oss << stringIntMap;
    std::string output = oss.str();
    
    // Check all keys and values
    EXPECT_NE(output.find("alpha"), std::string::npos);
    EXPECT_NE(output.find("beta"), std::string::npos);
    EXPECT_NE(output.find("gamma"), std::string::npos);
    EXPECT_NE(output.find("1"), std::string::npos);
    EXPECT_NE(output.find("2"), std::string::npos);
    EXPECT_NE(output.find("3"), std::string::npos);
}

TEST_F(MapTests, StringStringMapStream) {
    std::ostringstream oss;
    oss << stringStringMap;
    std::string output = oss.str();
    
    EXPECT_NE(output.find("key1"), std::string::npos);
    EXPECT_NE(output.find("value1"), std::string::npos);
    EXPECT_NE(output.find("key2"), std::string::npos);
    EXPECT_NE(output.find("value2"), std::string::npos);
}

TEST_F(MapTests, IntDoubleMapStream) {
    std::ostringstream oss;
    oss << intDoubleMap;
    std::string output = oss.str();
    
    EXPECT_NE(output.find("1"), std::string::npos);
    EXPECT_NE(output.find("2"), std::string::npos);
    EXPECT_NE(output.find("1.5"), std::string::npos);
    EXPECT_NE(output.find("2.5"), std::string::npos);
}

TEST_F(MapTests, EmptyMapStream) {
    std::map<std::string, int> emptyMap;
    std::ostringstream oss;
    oss << emptyMap;
    std::string output = oss.str();
    
    // Empty map should still produce valid output format
    EXPECT_GT(output.length(), 0);
}

TEST_F(MapTests, MapFormatting) {
    std::ostringstream oss;
    oss << stringIntMap;
    std::string output = oss.str();
    
    // Check basic formatting elements (braces, commas, etc)
    EXPECT_NE(output.find("{"), std::string::npos);
    EXPECT_NE(output.find("}"), std::string::npos);
    EXPECT_NE(output.find(","), std::string::npos);
}
