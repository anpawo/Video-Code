/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** grayscale
*/

#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>

#include "transformation/transformation.hpp"

void transformation::grayscale(std::shared_ptr<IInput>& input, [[maybe_unused]] const json::object_t& args)
{
    size_t start = args.at("start");
    bool persistent = args.at("persistent");

    input->addTransformation(start, persistent, "grayscale", [](Frame& frame) {
        for (int y = 0; y < frame.mat.rows; y++) {
            cv::Vec4b* row = frame.mat.ptr<cv::Vec4b>(y);
            for (int x = 0; x < frame.mat.cols; x++) {
                cv::Vec4b& p = row[x];
                uchar gray = static_cast<uchar>(0.299 * p[2] + 0.587 * p[1] + 0.114 * p[0]);
                p = cv::Vec4b(gray, gray, gray, p[3]);
            }
        }
    });
}
