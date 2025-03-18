#include <gtest/gtest.h>
#include "transformation/transformation.hpp"
#include "input/concrete/ABCConcreteInput.hpp"

class MockInput : public ABCConcreteInput {
public:
    MockInput(std::vector<Frame>&& frames) : ABCConcreteInput(std::move(frames)) {}
};

TEST(FadeTransformationTest, FadeInLeft) {
    std::vector<Frame> frames;
    frames.emplace_back(cv::Mat::zeros(10, 10, CV_8UC4));
    auto input = std::make_shared<MockInput>(std::move(frames));

    nlohmann::json args;
    args["sides"] = {"left"};
    args["startOpacity"] = 0.0f;
    args["endOpacity"] = 1.0f;
    args["affectTransparentPixel"] = true;

    transformation::fade(input, *(new Register()), args);

    auto frame = input->begin()->_mat;
    EXPECT_EQ(frame.at<cv::Vec4b>(0, 0)[3], 0);
    EXPECT_EQ(frame.at<cv::Vec4b>(0, 9)[3], 255);
}

TEST(FadeTransformationTest, FadeInRight) {
    std::vector<Frame> frames;
    frames.emplace_back(cv::Mat::zeros(10, 10, CV_8UC4));
    auto input = std::make_shared<MockInput>(std::move(frames));

    nlohmann::json args;
    args["sides"] = {"right"};
    args["startOpacity"] = 0.0f;
    args["endOpacity"] = 1.0f;
    args["affectTransparentPixel"] = true;

    transformation::fade(input, *(new Register()), args);

    auto frame = input->begin()->_mat;
    EXPECT_EQ(frame.at<cv::Vec4b>(0, 0)[3], 255);
    EXPECT_EQ(frame.at<cv::Vec4b>(0, 9)[3], 0);
}

TEST(FadeTransformationTest, FadeInUp) {
    std::vector<Frame> frames;
    frames.emplace_back(cv::Mat::zeros(10, 10, CV_8UC4));
    auto input = std::make_shared<MockInput>(std::move(frames));

    nlohmann::json args;
    args["sides"] = {"up"};
    args["startOpacity"] = 0.0f;
    args["endOpacity"] = 1.0f;
    args["affectTransparentPixel"] = true;

    transformation::fade(input, *(new Register()), args);

    auto frame = input->begin()->_mat;
    EXPECT_EQ(frame.at<cv::Vec4b>(0, 0)[3], 0);
    EXPECT_EQ(frame.at<cv::Vec4b>(9, 0)[3], 255);
}

TEST(FadeTransformationTest, FadeInDown) {
    std::vector<Frame> frames;
    frames.emplace_back(cv::Mat::zeros(10, 10, CV_8UC4));
    auto input = std::make_shared<MockInput>(std::move(frames));

    nlohmann::json args;
    args["sides"] = {"down"};
    args["startOpacity"] = 0.0f;
    args["endOpacity"] = 1.0f;
    args["affectTransparentPixel"] = true;

    transformation::fade(input, *(new Register()), args);

    auto frame = input->begin()->_mat;
    EXPECT_EQ(frame.at<cv::Vec4b>(0, 0)[3], 255);
    EXPECT_EQ(frame.at<cv::Vec4b>(9, 0)[3], 0);
}
