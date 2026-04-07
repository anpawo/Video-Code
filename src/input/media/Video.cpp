/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/media/Video.hpp"

#include <opencv2/imgcodecs.hpp>
#include <opencv2/opencv.hpp>
#include <utility>

#include "input/AInput.hpp"
#include "opencv2/videoio.hpp"
#include "utils/Exception.hpp"

Video::Video(json::object_t&& args)
    : AInput(std::move(args))
{
    std::string filepath = _baseArgs.at("filepath");

    _video.open(filepath);

    if (!_video.isOpened()) {
        throw Error("Could not load Video: " + filepath);
    }

    _sourceFrameCount = static_cast<size_t>(_video.get(cv::CAP_PROP_FRAME_COUNT));
    _sourceFps = _video.get(cv::CAP_PROP_FPS);

    if (_sourceFrameCount == 0) {
        throw Error("Video has no frames: " + filepath);
    }

    if (_sourceFps <= 0) {
        _sourceFps = 30;
    }

    // Convert source frame count to project frame count based on target FPS
    double projectFps = _baseArgs.count("projectFps") ? _baseArgs.at("projectFps").get<double>() : _sourceFps;
    double durationSec = static_cast<double>(_sourceFrameCount) / _sourceFps;
    _nbFrame = static_cast<size_t>(durationSec * projectFps);

    if (_nbFrame == 0) {
        _nbFrame = 1;
    }
}

cv::Mat Video::getBaseMatrix(const json::object_t& args)
{
    size_t index = args.at("index");

    // Map project frame index to source frame index for FPS conversion
    double projectFps = _baseArgs.count("projectFps") ? _baseArgs.at("projectFps").get<double>() : _sourceFps;
    size_t sourceIndex = static_cast<size_t>(
        static_cast<double>(index) * _sourceFps / projectFps
    );

    if (sourceIndex >= _sourceFrameCount) {
        sourceIndex = _sourceFrameCount - 1;
    }

    cv::Mat frame;

    while (true) {
        _video.set(cv::CAP_PROP_POS_FRAMES, static_cast<double>(sourceIndex));
        _video.read(frame);

        if (frame.empty()) {
            if (sourceIndex == _sourceFrameCount - 1) {
                _sourceFrameCount--;
                if (_sourceFrameCount == 0) {
                    throw Error("Video has no frames: " + _baseArgs.at("filepath").get<std::string>());
                }
            }
            sourceIndex--;
        } else {
            break;
        }
    }

    if (frame.channels() != 4) {
        cv::cvtColor(frame, frame, cv::COLOR_BGR2BGRA);
    }

    return frame;
}
