/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <nlohmann/json.hpp>
#include <opencv2/core/mat.hpp>

struct IEffect
{
    virtual ~IEffect() = default;

    ///< The index only matters for effects over time, e.g. fadeIn.
    virtual void render(cv::Mat&, int) = 0;
};
