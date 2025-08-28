/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <functional>

#include "input/Frame.hpp"

class IInput
{
public:

    IInput() = default;
    virtual ~IInput() = default;

    virtual void flushTransformation() = 0;

    virtual void apply(const std::string& name, const json::object_t& args) = 0;

    virtual void setBase(cv::Mat&& mat) = 0;

    ///< Add a transformation
    virtual void addTransformation(size_t index, std::function<void(Frame&)>&& f) = 0;

    ///< Generate next frame
    virtual Frame& generateNextFrame() = 0;

    ///< Get the last frame generated
    virtual Frame& getLastFrame() = 0;

    ///< Overlay the last frame generated
    virtual void overlayLastFrame(cv::Mat& background) = 0;

    ///< Did the Input change ?
    virtual bool frameHasChanged() = 0;
};
