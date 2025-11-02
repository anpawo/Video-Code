#include <gtest/gtest.h>
#include "window/Window.hpp"
#include "input/Frame.hpp"
#include <QApplication>
#include <QImage>

class WindowTests : public ::testing::Test {
protected:
    void SetUp() override {
        // Ensure we have a QApplication instance for the tests
        if (!qApp) {
            static int argc = 1;
            static char* argv[] = { (char*)"dummy" };
            new QApplication(argc, argv);
        }
        
        // Create test frame data
        testFrame.metadata.width = 640;
        testFrame.metadata.height = 480;
        // Create dummy data for the frame
        testFrame.data = cv::Mat(480, 640, CV_8UC3, cv::Scalar(255, 0, 0));
    }

    Frame testFrame;
};

TEST_F(WindowTests, ConstructorInitialization) {
    // Check Qt environment
    EXPECT_NE(qApp, nullptr);
    
    // Create window with test dimensions
    Window window(640, 480);
    EXPECT_EQ(window.width(), 640);
    EXPECT_EQ(window.height(), 480);
}

TEST_F(WindowTests, SetFrameValidation) {
    Window window(640, 480);
    
    // Test with valid frame
    EXPECT_NO_THROW(window.set_frame(testFrame));
    
    // Test with invalid frame dimensions
    Frame invalidFrame = testFrame;
    invalidFrame.metadata.width = 0;
    invalidFrame.metadata.height = 0;
    EXPECT_THROW(window.set_frame(invalidFrame), std::exception);
}

TEST_F(WindowTests, ResizeHandling) {
    Window window(640, 480);
    
    // Test resizing window
    window.resize(800, 600);
    EXPECT_EQ(window.width(), 800);
    EXPECT_EQ(window.height(), 600);
    
    // Test minimum size constraints
    window.resize(0, 0);
    EXPECT_GT(window.width(), 0);
    EXPECT_GT(window.height(), 0);
}

TEST_F(WindowTests, FrameScaling) {
    // Test that frames are properly scaled when window and frame sizes differ
    Window window(1280, 720);  // Different from test frame size
    EXPECT_NO_THROW(window.set_frame(testFrame));
}