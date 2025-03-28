/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/concrete/media/Video.hpp"

#include <opencv2/imgcodecs.hpp>
#include <utility>
#include <vector>

#include "opencv2/core/mat.hpp"
#include "opencv2/imgproc.hpp"
#include "opencv2/videoio.hpp"
#include "utils/Exception.hpp"

Video::Video(json::object_t&& args)
    : ABCConcreteInput(std::move(args))
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

        _frames.push_back(Frame(std::move(currentFrame)));
    }
}
