/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** grayscale
*/

#include <opencv2/opencv.hpp>

#include "transformation/transformation.hpp"

void transformation::grayscale(IterableInput input, [[maybe_unused]] const json::object_t &args)
{
    for (auto &[frame, _] : input) {
        for (int y = 0; y < frame.rows; y++) {
            for (int x = 0; x < frame.cols; x++) {
                cv::Vec4b &pixel = frame.at<cv::Vec4b>(y, x);
                uchar gray_value = static_cast<uchar>(0.299 * pixel[2] + 0.587 * pixel[1] + 0.114 * pixel[0]);
                pixel = cv::Vec4b(gray_value, gray_value, gray_value, pixel[3]);
            }
        }
    }
}
