/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** AInput
*/

#include "input/AInput.hpp"

#include <cassert>
#include <memory>

#include "input/IInput.hpp"
#include "transformation/transformation.hpp"

AInput::AInput(json::object_t&& args)
    : _args(std::move(args))
{
}

void AInput::flushTransformation()
{
    _flushedTransformationIndex = _transformations.size();
}

void AInput::apply(const std::string& name, const json::object_t& args)
{
    std::shared_ptr<IInput> i(this, [](IInput*) {});

    transformation::map.at(name)(i, args);
}

void AInput::setBase(cv::Mat&& mat)
{
    _base = std::move(mat);
    if (_lastFrame) {
        _lastFrame = std::make_unique<Frame>(_base.clone(), _lastFrame->meta);
    } else {
        _lastFrame = std::make_unique<Frame>(_base.clone());
    }
}

void AInput::addTransformation(size_t index, std::function<void(Frame&)>&& f)
{
    ///< Take into account used stuff
    while (_transformations.size() <= index + _flushedTransformationIndex) {
        _transformations.push_back({});
        _setters.push_back({});
    }
    _transformations[index + _flushedTransformationIndex].push_back(f);
}

void AInput::addSetter(size_t index, std::function<void(json::object_t&)>&& f)
{
    ///< Take into account used stuff
    while (_setters.size() <= index + _flushedTransformationIndex) {
        _transformations.push_back({});
        _setters.push_back({});
    }
    _setters[index + _flushedTransformationIndex].push_back(f);
}

Frame& AInput::generateNextFrame()
{
    if (_transformationIndex == _transformations.size()) {
        _frameHasChanged = false;
        return getLastFrame();
    } else {
        _frameHasChanged = true;
    }

    /// Apply the setters
    bool constructNeeded = false;

    for (const auto& s : _setters[_transformationIndex]) {
        s(getArgs());
        constructNeeded = true;
    }
    if (constructNeeded) {
        construct();
    }

    /// Reset the matrix but keep the metadata
    getLastFrame().mat = _base.clone();

    /// Apply the transformations
    for (const auto& t : _transformations[_transformationIndex]) {
        t(getLastFrame());
    }

    _transformationIndex += 1;
    return getLastFrame();
}

Frame& AInput::getLastFrame()
{
    return *_lastFrame;
}

void AInput::overlayLastFrame(cv::Mat& background)
{
    const Frame& frame = generateNextFrame();

    const auto& overlay = frame.mat;
    auto meta = frame.meta;
    meta.position.x += meta.align.x * overlay.cols;
    meta.position.y += meta.align.y * overlay.rows;

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

bool AInput::frameHasChanged()
{
    return _frameHasChanged;
}

json::object_t& AInput::getArgs()
{
    return _args;
}

void AInput::construct()
{
    // Does nothing, the Input doesn't have any arguments that would affect it.
}
