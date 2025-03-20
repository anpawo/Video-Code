/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#include "input/concrete/text/Text.hpp"

#include <vector>

#include "input/Frame.hpp"
#include "opencv2/core/types.hpp"

Text::Text(const std::string &text, double fontSize, int fontThickness, const std::vector<int> &color, float duration, int framerate, int font)
    : _text(text)
{
    int baseLine = 0;

    // get the size of the text and the baseline (line where letters sit)
    cv::Size size = cv::getTextSize(text, font, fontSize, fontThickness, &baseLine);

    cv::Mat bg = cv::Mat(size.height + baseLine, size.width, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0));

    cv::putText(bg, text, cv::Point(0, size.height), font, fontSize, cv::Scalar(color[0], color[1], color[2], color[3]), fontThickness, cv::LINE_AA);

    for (size_t i = framerate * duration; i; i--) {
        _frames.push_back(Frame(bg.clone()));
    }
}
