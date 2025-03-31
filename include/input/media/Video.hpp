/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Video
*/

#pragma once

#include "input/AInput.hpp"

class Video final : public AInput
{
public:

    Video(json::object_t&& args);
    ~Video() = default;

    void generateNextFrame() final;

private:

    std::vector<cv::Mat> _frames;

    size_t _frameIndex{0};
};
