/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Group
*/

#include "input/composite/Group.hpp"

#include <algorithm>
#include <utility>
#include <vector>

static void overlayFrame(cv::Mat &background, const Frame &frame)
{
    const auto &meta = frame._meta;
    const auto &overlay = frame._mat;

    // Calculate the source rectangle
    int srcX = std::max(0, -meta.x);
    int srcY = std::max(0, -meta.y);
    int srcW = std::min(overlay.cols - srcX, background.cols);
    int srcH = std::min(overlay.rows - srcY, background.rows);

    // Calculate the destination rectangle
    int dstX = std::max(0, meta.x);
    int dstY = std::max(0, meta.y);
    int dstW = srcW;
    int dstH = srcH;

    // Ensure the destination rectangle is within the frame bounds
    dstW = std::min(dstW, background.cols - dstX);
    dstH = std::min(dstH, background.rows - dstY);

    // Adjust the source rectangle if the destination rectangle was reduced
    srcW = dstW;
    srcH = dstH;

    // Define the source and destination regions
    cv::Rect src(srcX, srcY, srcW, srcH);
    cv::Rect dst(dstX, dstY, dstW, dstH);

    // Only copy if we have valid regions
    if (src.width > 0 && src.height > 0 && dst.width > 0 && dst.height > 0) {
        for (int y = 0; y < src.height; y++) {
            for (int x = 0; x < src.width; x++) {
                const cv::Vec4b &bgPixel = background.at<cv::Vec4b>(y + dst.y, x + dst.x);
                const cv::Vec4b &ovPixel = overlay.at<cv::Vec4b>(y + src.y, x + src.x);

                const float alphaBg = bgPixel[3] / 255.0f;
                const float alphaOv = ovPixel[3] / 255.0f;

                cv::Vec4b tmp;
                for (int i = 0; i < 3; i++) {
                    tmp[i] = static_cast<uchar>(
                        (ovPixel[i] * alphaOv + bgPixel[i] * (1.0f - alphaOv))
                    );
                }
                tmp[3] = (alphaBg + alphaOv * (1.0f - alphaBg)) * 255.0f;

                background.at<cv::Vec4b>(y + dst.y, x + dst.x) = tmp;
            }
        }
    }
}

Group::Group(const std::vector<std::shared_ptr<IInput>> &inputs, const json::object_t &args)
{
    const std::vector<size_t> &composition = args.at("inputs");
    std::vector<std::pair<std::vector<Frame>::iterator, std::vector<Frame>::iterator>> iterators;

    for (auto i : composition) {
        iterators.push_back({inputs[i]->begin(), inputs[i]->end()});
    }

    while (iterators.size()) {
        cv::Mat mat = cv::Mat(1080, 1920, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0));

        for (auto &it : iterators) {
            if (it.first == it.second) {
                continue;
            }

            overlayFrame(mat, *it.first);
            it.first++;
        }
        _frames.push_back(Frame(std::move(mat)));

        iterators.erase(
            std::remove_if(
                iterators.begin(),
                iterators.end(),
                [](const std::pair<std::vector<Frame>::iterator, std::vector<Frame>::iterator> &i) {
                    return i.first == i.second;
                }
            ),
            iterators.end()
        );
    }
}
