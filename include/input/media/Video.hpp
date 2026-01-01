/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Video
*/

#pragma once

#include <opencv2/videoio.hpp>

#include "input/AInput.hpp"

class Video final : public AInput
{
public:

    Video(json::object_t&& args);
    ~Video() = default;

    cv::Mat getBaseMatrix(const json::object_t& args);

    size_t _nbFrame{0};

private:

    cv::VideoCapture _video;
};
