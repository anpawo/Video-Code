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

Video::Video(const std::string &inputName)
    : _inputName(inputName)
{
    cv::VideoCapture video(inputName, cv::CAP_FFMPEG);

    if (!video.isOpened())
    {
        throw Error("Could not load Video: " + inputName);
    }

    while (true)
    {
        cv::Mat currentFrame;

        video >> currentFrame;

        if (currentFrame.empty())
        {
            break;
        }

        if (currentFrame.channels() != 4)
        {
            cv::cvtColor(currentFrame, currentFrame, cv::COLOR_BGR2BGRA);
        }

        _frames.push_back(std::move(currentFrame));
    }
}
