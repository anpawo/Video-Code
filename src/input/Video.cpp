/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/Video.hpp"

#include <opencv2/imgcodecs.hpp>
#include <utility>
#include <vector>

#include "opencv2/core/mat.hpp"
#include "opencv2/imgproc.hpp"
#include "opencv2/videoio.hpp"
#include "utils/Exception.hpp"

static std::vector<cv::Mat> loadFrames(const std::string& inputName)
{
    cv::VideoCapture video(inputName, cv::CAP_FFMPEG);

    if (!video.isOpened()) {
        throw Error("Invalid Video: " + inputName);
    }

    std::vector<cv::Mat> frames{};
    cv::Mat frame{};

    while (true) {
        video >> frame;

        if (frame.channels() == 3) {
            cv::cvtColor(frame, frame, cv::COLOR_BGR2BGRA);
        }

        if (frame.empty()) {
            break;
        }

        frames.push_back(frame.clone());
    }

    return frames;
}

Video::Video(std::string&& inputName)
    : _AInput(loadFrames(inputName))
    , _inputName(std::forward<std::string&&>(inputName))
{
}
