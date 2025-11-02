#include <gtest/gtest.h>
#include "input/Frame.hpp"
#include <opencv2/opencv.hpp>

namespace VC {

class FrameTests : public ::testing::Test {
protected:
    void SetUp() override {
        // Set up test environment
    }
};

TEST_F(FrameTests, V2OperationsWork) {
    v2f pos{1.0f, 2.0f};
    EXPECT_FLOAT_EQ(pos.x, 1.0f);
    EXPECT_FLOAT_EQ(pos.y, 2.0f);
    
    v2f pos2{3.0f, 4.0f};
    // No operator+ is defined on v2; test component-wise values instead
    EXPECT_FLOAT_EQ(pos2.x, 3.0f);
    EXPECT_FLOAT_EQ(pos2.y, 4.0f);
}

TEST_F(FrameTests, MetadataInitializesCorrectly) {
    Metadata meta;
    EXPECT_EQ(meta.position.x, 0); // Should initialize to {0, 0}
    EXPECT_EQ(meta.position.y, 0);
    EXPECT_FLOAT_EQ(meta.align.x, alignRatio.at("center")); // Should center by default
    EXPECT_FLOAT_EQ(meta.align.y, alignRatio.at("center"));
    // scale removed from Metadata in this codebase
    EXPECT_EQ(meta.rotation, 0); // Should initialize to 0
}

TEST_F(FrameTests, FrameConstructsWithValidData) {
    cv::Mat mat(100, 100, CV_8UC3); // Create test image
    Frame frame(std::move(mat));
    EXPECT_FALSE(frame.mat.empty());
    EXPECT_EQ(frame.meta.position.x, 0); // Should have default metadata
    EXPECT_EQ(frame.meta.position.y, 0);
}

} // namespace VC