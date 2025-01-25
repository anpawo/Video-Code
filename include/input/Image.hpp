/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#pragma once

#include <string>

#include "input/_AInput.hpp"

class Image : public _AInput {
public:

    Image(std::string&& inputName);
    ~Image() = default;

    std::vector<cv::Mat> loadFrames(const std::string& inputName) final;

private:
};
