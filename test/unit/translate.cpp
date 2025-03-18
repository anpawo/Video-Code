#include <gtest/gtest.h>
#include "transformation/transformation.hpp"
#include "input/concrete/ABCConcreteInput.hpp"

class MockInput : public ABCConcreteInput {
public:
    MockInput(std::vector<Frame>&& frames) : ABCConcreteInput(std::move(frames)) {}
};

TEST(TranslateTransformationTest, TranslateToNewPosition) {
    std::vector<Frame> frames;
    frames.emplace_back(cv::Mat::zeros(10, 10, CV_8UC4), Metadata{0, 0});
    auto input = std::make_shared<MockInput>(std::move(frames));

    nlohmann::json args;
    args["x"] = 100;
    args["y"] = 100;

    transformation::translate(input, *(new Register()), args);

    auto meta = input->begin()->_meta;
    EXPECT_EQ(meta.x, 100);
    EXPECT_EQ(meta.y, 100);
}

TEST(TranslateTransformationTest, TranslateWithMultipleFrames) {
    std::vector<Frame> frames;
    frames.emplace_back(cv::Mat::zeros(10, 10, CV_8UC4), Metadata{0, 0});
    frames.emplace_back(cv::Mat::zeros(10, 10, CV_8UC4), Metadata{0, 0});
    auto input = std::make_shared<MockInput>(std::move(frames));

    nlohmann::json args;
    args["x"] = 100;
    args["y"] = 100;

    transformation::translate(input, *(new Register()), args);

    auto meta1 = input->begin()->_meta;
    auto meta2 = std::next(input->begin())->_meta;
    EXPECT_EQ(meta1.x, 100);
    EXPECT_EQ(meta1.y, 100);
    EXPECT_EQ(meta2.x, 100);
    EXPECT_EQ(meta2.y, 100);
}
