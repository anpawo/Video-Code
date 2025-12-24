/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#pragma once

#include <opencv2/core/mat.hpp>

#include "input/AInput.hpp"

class Image final : public AInput
{
public:

    Image(json::object_t&& args);
    ~Image() = default;

    cv::Mat getBaseMatrix(const json::object_t& args);
};
