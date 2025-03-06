/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#pragma once

#include <string>

#include "input/concrete/ABCConcreteInput.hpp"
#include "opencv2/imgproc.hpp"

class Text final : public ABCConcreteInput
{
public:

    Text(const std::string &text, double fontSize, int fontThickness, const std::vector<int> &color, int font = cv::FONT_HERSHEY_SIMPLEX);
    ~Text() = default;

private:

    const std::string _text;
};
