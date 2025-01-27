/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Slice
*/

#pragma once

#include "input/_AInput.hpp"

class Slice : public _AInput {
public:

    Slice(std::shared_ptr<_IInput> src, int lowerBound, int upperBound);
    ~Slice() = default;

private:

    /**
     * @ input src
     */
    const std::shared_ptr<_IInput> _src;

    /**
     * @ src bounds
     */
    const int _lowerBound;
    const int _upperBound;
};
