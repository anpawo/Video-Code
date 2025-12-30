#include <gtest/gtest.h>

#include "input/IInput.hpp"

// Minimal compile-time sanity tests for IInput

class MockInput : public AInput
{
public:

    MockInput()
        : AInput(json::object())
    {
        // Create test frames
        for (int i = 0; i < 10; i++) {
            _frames.push_back(Frame(cv::Mat(100, 100, CV_8UC3)));
        }
    }

    // Implementation of pure virtual methods from IInput
    void construct() override {}

    std::vector<Frame>& getFrames() override { return _frames; }

    // No need to re-declare iterator/size methods; use ones from AInput
};

class IterableTests : public ::testing::Test
{
protected:

    void SetUp() override
    {
        _mockInput = std::make_shared<MockInput>();
    }

    std::shared_ptr<MockInput> _mockInput;
};

TEST_F(IterableTests, DefaultConstruction)
{
    // Test with null start/end times (full range)
    IterableInput iterable(_mockInput, json(nullptr), json(nullptr), 60);
    EXPECT_EQ(iterable._nbFrames, _mockInput->size());
}

TEST_F(IterableTests, PartialRange)
{
    // Test with explicit start/end times
    IterableInput iterable(_mockInput, json(1.0f), json(2.0f), 60);
    EXPECT_EQ(iterable._nbFrames, 60); // 1 second worth of frames at 60fps
}

TEST_F(IterableTests, NegativeTime)
{
    // Test with negative times (relative to end)
    IterableInput iterable(_mockInput, json(-2.0f), json(-1.0f), 60);
    EXPECT_EQ(iterable._nbFrames, 60);
}

TEST_F(IterableTests, Iteration)
{
    IterableInput iterable(_mockInput, json(nullptr), json(nullptr), 60);
    size_t count = 0;
    for (const auto& frame : iterable) {
        EXPECT_FALSE(frame.mat.empty());
        count++;
    }
    EXPECT_EQ(count, _mockInput->size());
}

} // namespace VC
