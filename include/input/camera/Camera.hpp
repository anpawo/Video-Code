/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#pragma once

#include "input/AInput.hpp"

class Camera final : public AInput
{
public:

    Camera(cv::Mat&& mat, json::object_t&& args);
    ~Camera() = default;

    ///< Reset it to the black frame
    void reset();

    ///< Consumes setPosition if any and get the position of the last frame
    const v2i& getPosition();
};
