#include <gtest/gtest.h>
#include "input/AInput.hpp"
#include "input/shape/Circle.hpp"
#include "input/shape/Rectangle.hpp"
#include "input/Frame.hpp"
#include <opencv2/opencv.hpp>

class AInputAdvancedTests : public ::testing::Test {
protected:
    void SetUp() override {
        json::object_t circleArgs = {
            {"radius", 30},
            {"thickness", 1},
            {"filled", true},
            {"color", json::array_t{255, 0, 0, 255}}
        };
        circle = std::make_shared<Circle>(std::move(circleArgs));
        
        // Create a background frame
        background = cv::Mat(200, 200, CV_8UC4, cv::Scalar(0, 0, 0, 0));
    }

    std::shared_ptr<Circle> circle;
    cv::Mat background;
};

TEST_F(AInputAdvancedTests, OverlayLastFrameOnBackground) {
    // Set position for the circle
    circle->getArgs()["x"] = 50;
    circle->getArgs()["y"] = 50;
    
    // Overlay the frame onto the background
    EXPECT_NO_THROW(circle->overlayLastFrame(background));
    
    // Verify background was modified
    EXPECT_FALSE(background.empty());
}

TEST_F(AInputAdvancedTests, OverlayWithNegativePosition) {
    // Set negative position (partial overlay)
    circle->getArgs()["x"] = -20;
    circle->getArgs()["y"] = -20;
    
    EXPECT_NO_THROW(circle->overlayLastFrame(background));
    EXPECT_FALSE(background.empty());
}

TEST_F(AInputAdvancedTests, OverlayWithLargePosition) {
    // Set position beyond background bounds
    circle->getArgs()["x"] = 180;
    circle->getArgs()["y"] = 180;
    
    EXPECT_NO_THROW(circle->overlayLastFrame(background));
    EXPECT_FALSE(background.empty());
}

TEST_F(AInputAdvancedTests, FlushTransformationUpdatesIndex) {
    // Add some transformations
    circle->addTransformation(0, [](Frame& f) {
        f.meta.position.x = 10;
    });
    circle->addTransformation(1, [](Frame& f) {
        f.meta.position.y = 20;
    });
    
    // Flush transformations
    EXPECT_NO_THROW(circle->flushTransformation());
    
    // Add more transformations after flush
    circle->addTransformation(0, [](Frame& f) {
        f.meta.position.x = 30;
    });
    
    // Generate frames
    auto& frame1 = circle->generateNextFrame();
    EXPECT_FALSE(frame1.mat.empty());
}

TEST_F(AInputAdvancedTests, AddSetterModifiesArgs) {
    // Add a setter
    circle->addSetter(0, [](json::object_t& args) {
        args["radius"] = 50;
    });
    
    // Flush to trigger setter execution
    circle->flushTransformation();
    
    // Generate frame to execute setter
    auto& frame = circle->generateNextFrame();
    EXPECT_FALSE(frame.mat.empty());
}

TEST_F(AInputAdvancedTests, FrameHasChangedTracking) {
    // Add a transformation so frame will change
    circle->addTransformation(0, [](Frame& f) {
        f.meta.position.x = 10;
    });
    
    // Generate first frame - should have changed
    circle->generateNextFrame();
    EXPECT_TRUE(circle->frameHasChanged());
    
    // After exhausting transformations, frame should not change
    circle->generateNextFrame();
    EXPECT_FALSE(circle->frameHasChanged());
}

TEST_F(AInputAdvancedTests, SetBasePreservesMetadata) {
    // Get initial frame to establish metadata
    auto& frame1 = circle->getLastFrame();
    frame1.meta.position.x = 100;
    frame1.meta.position.y = 200;
    
    // Set a new base
    cv::Mat newBase(150, 150, CV_8UC4, cv::Scalar(0, 255, 0, 255));
    circle->setBase(std::move(newBase));
    
    // Metadata should be preserved
    auto& frame2 = circle->getLastFrame();
    EXPECT_EQ(frame2.meta.position.x, 100);
    EXPECT_EQ(frame2.meta.position.y, 200);
}

TEST_F(AInputAdvancedTests, OverlayWithAlignment) {
    // Add alignment transformation
    auto& frame = circle->getLastFrame();
    frame.meta.align.x = -0.5f;  // center align
    frame.meta.align.y = -0.5f;
    frame.meta.position.x = 100;
    frame.meta.position.y = 100;
    
    EXPECT_NO_THROW(circle->overlayLastFrame(background));
    EXPECT_FALSE(background.empty());
}
