/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#pragma once

#include <opencv2/core/mat.hpp>

#include "input/AInput.hpp"

///< Only Class that stores a Matrix
class WebImage final : public AInput
{
public:

    WebImage(json::object_t&& args);
    ~WebImage() = default;

    cv::Mat getBaseMatrix(const json::object_t& args);

private:

    cv::Mat _base;
};
