/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <vector>

#include "input/Frame.hpp"
#include "input/IInput.hpp"

class ABCConcreteInput : public IInput
{
public:

    ABCConcreteInput() = default;
    ABCConcreteInput(std::vector<Frame>&& frames);
    ~ABCConcreteInput() = default;

    ///< Deep copy of `_frames`
    IInput* copy() final;

    ///< Iteration
    std::vector<Frame>::iterator begin() final;
    std::vector<Frame>::iterator end() final;

    ///< Size
    size_t size() final;

protected:

    std::vector<Frame> _frames{}; ///< Frames of the Input
};
