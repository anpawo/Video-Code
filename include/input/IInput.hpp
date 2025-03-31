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

    // ///< Deep copy of `_frames`
    // virtual IInput* copy() = 0;

    // ///< Iteration
    // virtual std::vector<Frame>::iterator begin() = 0;
    // virtual std::vector<Frame>::iterator end() = 0;
    // virtual Frame& back() = 0;

    // ///< Repeat
    // virtual void repeat(size_t n) = 0;

    // ///< Size
    // virtual size_t size() = 0;

    ///< Add a transformation
    virtual void addTransformation(std::function<void(Frame&)>&& f) = 0;

    ///< Generate next frame
    virtual void generateNextFrame() = 0;

    ///< Get the last frame generated
    virtual const Frame& getLastFrame() = 0;

    ///< Overlay the last frame generated
    virtual void overlayLastFrame(cv::Mat& background) = 0;

    ///< Did the Input change ?
    virtual bool hasChanged() = 0;
};
