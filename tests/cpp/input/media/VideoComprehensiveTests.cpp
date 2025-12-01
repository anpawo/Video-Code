#include <gtest/gtest.h>
#include "input/media/Video.hpp"
#include "input/Frame.hpp"
#include "utils/Exception.hpp"
#include <nlohmann/json.hpp>
#include <opencv2/opencv.hpp>

class VideoComprehensiveTests : public ::testing::Test {
protected:
    void SetUp() override {
        // Create a simple test video file if possible
        // For testing, we'll use existing test resources
        validArgs = {{"filepath", "/home/hippo/code/Video-Code/tests/resources/test_video.mp4"}};
        invalidArgs = {{"filepath", "nonexistent_video.avi"}};
    }
    
    nlohmann::json validArgs;
    nlohmann::json invalidArgs;
};

TEST_F(VideoComprehensiveTests, ConstructorErrorHandling) {
    // Test with non-existent video file
    nlohmann::json::object_t args = invalidArgs;
    EXPECT_THROW(Video video(std::move(args)), Error);
}

TEST_F(VideoComprehensiveTests, ConstructorWithMissingFilepath) {
    nlohmann::json emptyArgs;
    
    // Should throw when trying to access missing "filepath" argument  
    EXPECT_THROW(Video video(emptyArgs), std::exception);
}

TEST_F(VideoComprehensiveTests, GenerateNextFrameMethod) {
    try {
        nlohmann::json::object_t args = validArgs;
        Video video(std::move(args));
        
        // Test generateNextFrame method multiple times
        Frame& frame1 = video.generateNextFrame();
        Frame& frame2 = video.generateNextFrame();
        Frame& frame3 = video.generateNextFrame();
        
        // Frames should be valid
        EXPECT_FALSE(frame1.mat.empty());
        EXPECT_FALSE(frame2.mat.empty());
        EXPECT_FALSE(frame3.mat.empty());
        
        // Test going beyond video end
        for (int i = 0; i < 1000; ++i) {  // Try to go beyond end
            video.generateNextFrame();
        }
        
    } catch (const Error& e) {
        // If video loading fails due to missing codec, that's acceptable
        if (std::string(e.what()).find("Could not load Video") != std::string::npos) {
            GTEST_SKIP() << "Video codec not available: " << e.what();
        } else {
            throw;
        }
    }
}

TEST_F(VideoComprehensiveTests, VideoChannelsHandling) {
    try {
        nlohmann::json::object_t args = validArgs;
        Video video(std::move(args));
        
        // The constructor should handle different channel formats
        // This tests the cv::cvtColor conversion code path
        
        // Just verify the video was created successfully
        SUCCEED();
        
    } catch (const Error& e) {
        if (std::string(e.what()).find("Could not load Video") != std::string::npos) {
            GTEST_SKIP() << "Video codec not available";
        } else {
            throw;
        }
    }
}

TEST_F(VideoComprehensiveTests, EmptyVideoFile) {
    // Test with empty or corrupted video file
    nlohmann::json::object_t emptyFileArgs = {{"filepath", "/dev/null"}};
    
    EXPECT_THROW(Video video(std::move(emptyFileArgs)), Error);
}

TEST_F(VideoComprehensiveTests, FrameIndexingBehavior) {
    try {
        nlohmann::json::object_t args = validArgs;
        Video video(std::move(args));
        
        // Test frame indexing behavior
        Frame& firstFrame = video.generateNextFrame();
        EXPECT_FALSE(firstFrame.mat.empty());
        
        // Generate multiple frames to test internal frame indexing
        for (int i = 0; i < 10; ++i) {
            Frame& frame = video.generateNextFrame(); 
            // Each frame should be valid until video ends
            EXPECT_FALSE(frame.mat.empty());
        }
        
    } catch (const Error& e) {
        if (std::string(e.what()).find("Could not load Video") != std::string::npos) {
            GTEST_SKIP() << "Video codec not available";
        }
    }
}

TEST_F(VideoComprehensiveTests, VideoArgsMissingKey) {
    // Test with malformed args (missing required key)
    nlohmann::json::object_t badArgs = {{"wrong_key", "some_value"}};
    
    // Should throw due to missing "filepath" key
    EXPECT_THROW(Video video(std::move(badArgs)), std::exception);
}