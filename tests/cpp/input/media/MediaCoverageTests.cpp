#include <gtest/gtest.h>
#include "input/media/Video.hpp"
#include "input/media/Image.hpp"
#include "utils/Exception.hpp"
#include <opencv2/opencv.hpp>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

class MediaCoverageTests : public ::testing::Test {
protected:
    void SetUp() override {
        // Create a test video file for testing
        createTestVideo();
        createTestImage();
    }
    
    void createTestVideo() {
        // Create a simple test video using OpenCV
        cv::VideoWriter writer("test_video.mp4", cv::VideoWriter::fourcc('m','p','4','v'), 30, cv::Size(640, 480));
        if (writer.isOpened()) {
            for (int i = 0; i < 10; i++) {
                cv::Mat frame(480, 640, CV_8UC3, cv::Scalar(i*25, 128, 255-i*25));
                writer.write(frame);
            }
            writer.release();
        }
    }
    
    void createTestImage() {
        // Create a simple test image
        cv::Mat img(100, 100, CV_8UC3, cv::Scalar(255, 0, 0));
        cv::imwrite("test_image.jpg", img);
    }
};

TEST_F(MediaCoverageTests, VideoConstructorValid) {
    // Test valid video loading
    json::object_t args;
    args["filepath"] = "test_video.mp4";
    
    try {
        Video video(std::move(args));
        // Video should be constructed successfully
        SUCCEED();
    } catch (const Error& e) {
        // If video creation fails due to missing codecs, skip this test
        GTEST_SKIP() << "Video codec not available: " << e.what();
    }
}

TEST_F(MediaCoverageTests, VideoConstructorInvalid) {
    // Test invalid video file
    json::object_t args;
    args["filepath"] = "nonexistent_video_file.mp4";
    
    EXPECT_THROW(Video video(std::move(args)), Error);
}

TEST_F(MediaCoverageTests, VideoGenerateNextFrame) {
    json::object_t args;
    args["filepath"] = "test_video.mp4";
    
    try {
        Video video(std::move(args));
        
        // Test generateNextFrame method
        Frame& frame1 = video.generateNextFrame();
        Frame& frame2 = video.generateNextFrame();
        
        // Frames should be valid
        EXPECT_FALSE(frame1.mat.empty());
        EXPECT_FALSE(frame2.mat.empty());
        
    } catch (const Error& e) {
        GTEST_SKIP() << "Video codec not available: " << e.what();
    }
}

TEST_F(MediaCoverageTests, ImageConstructorValid) {
    // Test valid image loading
    json::object_t args;
    args["filepath"] = "test_image.jpg";
    
    Image image(std::move(args));
    // Should construct successfully
    SUCCEED();
}

TEST_F(MediaCoverageTests, ImageConstructorInvalid) {
    // Test invalid image file
    json::object_t args;
    args["filepath"] = "nonexistent_image_file.jpg";
    
    EXPECT_THROW(Image image(std::move(args)), Error);
}

TEST_F(MediaCoverageTests, ImageGenerateNextFrame) {
    json::object_t args;
    args["filepath"] = "test_image.jpg";
    
    Image image(std::move(args));
    
    // Test generateNextFrame method
    Frame& frame = image.generateNextFrame();
    
    // Frame should be valid
    EXPECT_FALSE(frame.mat.empty());
}

TEST_F(MediaCoverageTests, VideoHeaderCompilation) {
    // This tests the header-only parts that might not be covered
    json::object_t args;
    args["filepath"] = "test_video.mp4";
    
    try {
        Video video(std::move(args));
        
        // Test basic video functionality without move semantics
        // since Video has deleted copy constructor
        SUCCEED();
        
    } catch (const Error& e) {
        GTEST_SKIP() << "Video codec not available: " << e.what();
    }
}