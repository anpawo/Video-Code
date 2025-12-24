/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** grayscale
*/

#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>

#include "transformation/EffectFactory.hpp"

Grayscale::Grayscale(const json::object_t& _)
{
}

void Grayscale::render(cv::Mat& mat, int _)
{
    for (int y = 0; y < mat.rows; y++) {
        cv::Vec4b* row = mat.ptr<cv::Vec4b>(y);
        for (int x = 0; x < mat.cols; x++) {
            cv::Vec4b& p = row[x];
            uchar gray = static_cast<uchar>(0.299 * p[2] + 0.587 * p[1] + 0.114 * p[0]);
            p[0] = p[1] = p[2] = gray;
        }
    }

    ///< TODO: Opti
    // cv::parallel_for_(cv::Range(0, mat.rows), [&](const cv::Range& range) {
    //     for (int y = range.start; y < range.end; y++) {
    //         cv::Vec4b* row = mat.ptr<cv::Vec4b>(y);
    //         for (int x = 0; x < mat.cols; x++) {
    //             cv::Vec4b& p = row[x];
    //             uchar gray = static_cast<uchar>(0.299 * p[2] + 0.587 * p[1] + 0.114 * p[0]);
    //             p[0] = p[1] = p[2] = gray;
    //         }
    //     }
    // });
}

// void grayscale()
// {
//     size_t start = args.at("start");
//     bool persistent = args.at("persistent");

// input->addTransformation(start, persistent, "grayscale", [](Frame& frame) {
//     for (int y = 0; y < frame.mat.rows; y++) {
//         cv::Vec4b* row = frame.mat.ptr<cv::Vec4b>(y);
//         for (int x = 0; x < frame.mat.cols; x++) {
//             cv::Vec4b& p = row[x];
//             uchar gray = static_cast<uchar>(0.299 * p[2] + 0.587 * p[1] + 0.114 * p[0]);
//             p = cv::Vec4b(gray, gray, gray, p[3]);
//         }
//     }
// });
// }
