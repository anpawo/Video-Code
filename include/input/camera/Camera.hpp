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

    ///< Check _transformationIndex bounds
    void applySetters();

    ///< Generates the next frame without reseting the mat
    Frame& generateNextFrame() final;
};
