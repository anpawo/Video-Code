/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/media/Video.hpp"

#include <opencv2/imgcodecs.hpp>
#include <utility>

#include "input/AInput.hpp"
#include "opencv2/core/mat.hpp"
#include "opencv2/imgproc.hpp"
#include "opencv2/videoio.hpp"
#include "utils/Exception.hpp"

Video::Video(json::object_t&& args)
    : AInput(std::move(args))
{
    std::string filepath = _args.at("filepath");

    cv::VideoCapture video(filepath, cv::CAP_FFMPEG);

    if (!video.isOpened()) {
        throw Error("Could not load Video: " + filepath);
    }

    while (true) {
        cv::Mat currentFrame;

        video >> currentFrame;

        if (currentFrame.empty()) {
            break;
        }

        if (currentFrame.channels() != 4) {
            cv::cvtColor(currentFrame, currentFrame, cv::COLOR_BGR2BGRA);
        }

        _frames.push_back(std::move(currentFrame));
    }

    setBase(_frames[0].clone());
}

Frame& Video::generateNextFrame()
{
    bool videoEnded = false;

    if (_frameIndex < _frames.size()) {
        _base = std::move(_frames[_frameIndex]);
        _frameIndex += 1;
    } else {
        videoEnded = true;
    }

    AInput::generateNextFrame();

    _frameHasChanged |= !videoEnded;

    return getCurrentFrame();
}
