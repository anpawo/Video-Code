#include <gtest/gtest.h>

#include <nlohmann/json.hpp>
#include <opencv2/core/mat.hpp>

#include "input/AInput.hpp"
#include "input/Frame.hpp"

namespace videocode
{
    class TestInput : public AInput
    {
    public:

        TestInput()
            : AInput(nlohmann::json::object())
        {
            // Create an empty frame
            cv::Mat emptyMat(100, 100, CV_8UC3);
            setBase(std::move(emptyMat));
        }

        void construct() override
        {
            // Test implementation
        }

        // Test methods
        Frame& getFrame() { return generateNextFrame(); }

        void setPosition(const v2f& pos)
        {
            auto args = nlohmann::json::object();
            args["x"] = pos.x;
            args["y"] = pos.y;
            args["start"] = 0; // required by setPosition implementation
            apply("setPosition", args);
        }

        void setOpacity(float opacity)
        {
            auto args = nlohmann::json::object();
            args["opacity"] = opacity;
            apply("setOpacity", args);
        }
    };

    class AInputTests : public ::testing::Test
    {
    protected:

        void SetUp() override
        {
            // Set up test environment
        }
    };

    TEST_F(AInputTests, DefaultConstructor)
    {
        TestInput input;
        auto& frame = input.getFrame();

        // Check default values
        EXPECT_FLOAT_EQ(frame.meta.align.x, -0.5f); // center alignment
        EXPECT_FLOAT_EQ(frame.meta.align.y, -0.5f); // center alignment
        EXPECT_EQ(frame.meta.position.x, 0);
        EXPECT_EQ(frame.meta.position.y, 0);
        EXPECT_EQ(frame.meta.rotation, 0);
    }

    TEST_F(AInputTests, SetPosition)
    {
        TestInput input;
        v2f newPos(10.0f, 20.0f);
        input.setPosition(newPos);

        auto& frame = input.getFrame();
        EXPECT_EQ(frame.meta.position.x, 10);
        EXPECT_EQ(frame.meta.position.y, 20);
    }

    TEST_F(AInputTests, ValidFrameAfterConstruction)
    {
        TestInput input;
        input.construct();
        EXPECT_FALSE(input.getLastFrame().mat.empty());
    }
} // namespace videocode
