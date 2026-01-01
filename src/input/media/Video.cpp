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

    _nbFrame = static_cast<size_t>(_video.get(cv::CAP_PROP_FRAME_COUNT));

    if (_nbFrame == 0) {
        throw Error("Video has no frames: " + filepath);
    }
}

cv::Mat Video::getBaseMatrix(const json::object_t& args)
{
    size_t index = args.at("index");

    if (index >= _nbFrame) {
        index = _nbFrame - 1;
    }

    cv::Mat frame;

    while (true) {
        _video.set(cv::CAP_PROP_POS_FRAMES, static_cast<double>(index));
        _video.read(frame);

        if (frame.empty()) {
            if (index == _nbFrame - 1) {
                _nbFrame--;
                if (_nbFrame == 0) {
                    throw Error("Video has no frames: " + _baseArgs.at("filepath").get<std::string>());
                }
            }
            index--;
        } else {
            break;
        }
    }

    if (frame.channels() != 4) {
        cv::cvtColor(frame, frame, cv::COLOR_BGR2BGRA);
    }

    return frame;
}
