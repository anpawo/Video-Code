/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#include "input/text/Text.hpp"

#include <vector>

#include "opencv2/core/types.hpp"
#include "opencv2/imgproc.hpp"

Text::Text(json::object_t &&args)
    : AInput(std::move(args))
{
}

cv::Mat Text::getBaseMatrix(const json::object_t &args)
{
    const std::string &text = args.at("text");
    double fontSize = args.at("fontSize");
    int fontThickness = args.at("fontThickness");
    const std::vector<int> &color = args.at("color");
    int font = cv::FONT_HERSHEY_SIMPLEX;

    int baseLine = 0;

    // get the size of the text and the baseline (line where letters sit)
    cv::Size size = cv::getTextSize(text, font, fontSize, fontThickness, &baseLine);

    cv::Mat mat = cv::Mat(size.height + baseLine, size.width, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0));

    cv::putText(mat, text, cv::Point(0, size.height), font, fontSize, cv::Scalar(color[0], color[1], color[2], color[3]), fontThickness, cv::LINE_AA);

    return mat;
}
