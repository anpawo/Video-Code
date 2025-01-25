/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Video
*/

#pragma once

#include <string>

#include "input/_AInput.hpp"

class Video : public _AInput {
public:

    Video(std::string&& inputName);
    ~Video() = default;

    std::vector<cv::Mat> loadFrames(const std::string& inputName) final;

private:
};
