/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <nlohmann/json.hpp>
#include <opencv2/core/mat.hpp>

/*

Shaders affect anything pixel related in an Input

*/

struct IFragmentShader
{
    virtual ~IFragmentShader() = default;

    ///< Offset of the index
    virtual size_t start() const = 0;

    ///< The index only matters for effects over time, e.g. fadeIn.
    virtual void render(cv::Mat&, size_t) const = 0;
};
