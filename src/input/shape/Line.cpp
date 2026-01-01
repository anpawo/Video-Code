/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#include "input/shape/Line.hpp"

#include <cstddef>
#include <vector>

#include "opencv2/core/matx.hpp"
#include "opencv2/core/types.hpp"
#include "opencv2/imgproc.hpp"

Line::Line(json::object_t &&args)
    : AInput(std::move(args))
{
}

static void line(cv::Mat &bg, const size_t x, const size_t y, const size_t w, const size_t h, const cv::Vec4b &color)
{
    for (size_t iy = y; iy < h; iy++) {
        for (size_t ix = x; ix < w; ix++) {
            bg.at<cv::Vec4b>(iy, ix) = color;
        }
    }
}

cv::Mat Line::getBaseMatrix(const json::object_t &args)
{
    size_t l = args.at("length");
    size_t t = args.at("thickness");
    const std::vector<int> &color = args.at("color");
    bool rounded = args.at("rounded");
    const cv::Vec4b bgra = cv::Scalar(color[2], color[1], color[0], color[3]);
    cv::LineTypes lineType = cv::LINE_AA;
    int radius = t / 2;
    int cy = radius;
    int leftCx = radius;
    int rightCx = l - radius - 1;

    cv::Mat mat = cv::Mat(t, l, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0));

    size_t a = rounded ? t / 2 : 0;

    if (rounded) {
        cv::circle(mat, {leftCx, cy}, radius, bgra, cv::FILLED, lineType);
        cv::circle(mat, {rightCx, cy}, radius, bgra, cv::FILLED, lineType);
    }

    line(mat, a, 0, l - a, t, bgra); // left => right

    return mat;
}
