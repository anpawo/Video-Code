/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#include "input/concrete/shape/Rectangle.hpp"

#include <cmath>
#include <cstddef>
#include <vector>

#include "input/Frame.hpp"
#include "opencv2/core/matx.hpp"
#include "opencv2/core/types.hpp"
#include "opencv2/imgproc.hpp"

static void line(cv::Mat &bg, const size_t x, const size_t y, const size_t w, const size_t h, const cv::Vec4b &color)
{
    for (size_t iy = y; iy < h; iy++) {
        for (size_t ix = x; ix < w; ix++) {
            bg.at<cv::Vec4b>(iy, ix) = color;
        }
    }
}

Rectangle::Rectangle(const json::object_t &args, int framerate)
{
    size_t w = args.at("width");
    size_t h = args.at("height");
    size_t t = args.at("thickness");
    const std::vector<int> &color = args.at("color");
    size_t r = args.at("cornerRadius");
    bool filled = args.at("filled");
    float duration = args.at("duration");
    const cv::Vec4b bgra = cv::Scalar(color[2], color[1], color[0], color[3]);
    cv::LineTypes lineType = cv::LINE_AA;

    cv::Mat bg = cv::Mat(h, w, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0));

    size_t a = r ? t / 2 : 0;

    if (r) {
        cv::ellipse(bg, cv::Point2d(r + a, r + a), cv::Size(r, r), 180, 0, 90, bgra, t, lineType);
        cv::ellipse(bg, cv::Point2d(w - r - a - 1, r + a), cv::Size(r, r), 180, 90, 180, bgra, t, lineType);
        cv::ellipse(bg, cv::Point2d(w - r - a - 1, h - r - a - 1), cv::Size(r, r), 180, 180, 270, bgra, t, lineType);
        cv::ellipse(bg, cv::Point2d(r + a, h - r - a - 1), cv::Size(r, r), 180, 270, 360, bgra, t, lineType);
    }

    line(bg, r + a, 0, w - r - a, t, bgra);     // top
    line(bg, r + a, h - t, w - r - a, h, bgra); // bottom
    line(bg, w - t, r + a, w, h - r - a, bgra); // right
    line(bg, 0, r + a, t, h - r - a, bgra);     // left

    if (filled) {
        for (size_t y = 0; y < h; y++) {
            for (size_t x = w / 2; x < w; x++) {
                if (bg.at<cv::Vec4b>(y, x)[3] != bgra[3]) {
                    bg.at<cv::Vec4b>(y, x) = bgra;
                    continue;
                }
                break;
            }
            for (size_t x = w / 2 - 1; x > 0; x--) {
                if (bg.at<cv::Vec4b>(y, x)[3] != bgra[3]) {
                    bg.at<cv::Vec4b>(y, x) = bgra;
                    continue;
                }
                break;
            }
        }
    }

    for (size_t i = framerate * duration; i; i--) {
        _frames.push_back(Frame(bg.clone()));
    }
}
