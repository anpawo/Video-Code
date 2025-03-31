/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** AInput
*/

#include "input/AInput.hpp"

#include <cassert>
#include <memory>

AInput::AInput(json::object_t&& args)
    : _args(std::move(args))
{
}

void AInput::addTransformation(std::function<void(Frame&)>&& f)
{
}

void AInput::generateNextFrame()
{
    if (_transformationIndex == _transformations.size()) {
        _hasChanged = false;
        return;
    }

    /// Reset the matrix but keep the metadata
    _lastFrame->mat = _base->mat.clone();

    for (const auto& t : _transformations[_transformationIndex]) {
        t(*_lastFrame);
    }

    _transformationIndex += 1;
}

const Frame& AInput::getLastFrame()
{
    generateNextFrame();

    if (_lastFrame) {
        return *_lastFrame;
    }
    else {
        return *_base;
    }
}

void AInput::overlayLastFrame(cv::Mat& background)
{
    const Frame& frame = getLastFrame();

    const auto& meta = frame.meta;
    const auto& overlay = frame.mat;

    // Calculate the source rectangle
    int srcX = std::max(0, -meta.position.x);
    int srcY = std::max(0, -meta.position.y);
    int srcW = std::min(overlay.cols - srcX, background.cols);
    int srcH = std::min(overlay.rows - srcY, background.rows);

    // Calculate the destination rectangle
    int dstX = std::max(0, meta.position.x);
    int dstY = std::max(0, meta.position.y);
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
                const cv::Vec4b& bgPixel = background.at<cv::Vec4b>(y + dst.y, x + dst.x);
                const cv::Vec4b& ovPixel = overlay.at<cv::Vec4b>(y + src.y, x + src.x);

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

bool AInput::hasChanged()
{
    return _hasChanged;
}
