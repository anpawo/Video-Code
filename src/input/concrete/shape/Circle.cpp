/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#include "input/concrete/shape/Circle.hpp"

#include <vector>

#include "input/Frame.hpp"
#include "opencv2/core/types.hpp"
#include "opencv2/imgproc.hpp"

Circle::Circle(const json::object_t &args, int framerate)
{
    int radius = args.at("radius");
    int thickness = args.at("thickness");
    const std::vector<int> &color = args.at("color");
    float duration = args.at("duration");
    bool filled = args.at("filled");

    if (thickness == 0) {
        thickness = 1;
    }

    cv::Mat bg = cv::Mat(radius * 2, radius * 2, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0));

    cv::circle(bg, cv::Point(radius, radius), radius - thickness / 2 * !filled, cv::Scalar(color[2], color[1], color[0], color[3]), filled ? cv::FILLED : thickness, cv::LINE_AA);

    for (size_t i = framerate * duration; i; i--) {
        _frames.push_back(Frame(bg.clone()));
    }
}
