/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Slice
*/

#pragma once

#include <vector>

#include "input/composite/ABCCompositeInput.hpp"

class Slice final : public ABCCompositeInput
{
public:

    Slice(std::shared_ptr<IInput> input, int begin, int end);
    ~Slice() = default;

    ///< Deep copy of `this`
    IInput* copy();

    ///< Iteration
    virtual std::vector<Frame>::iterator begin();
    virtual std::vector<Frame>::iterator end();

    ///< Size
    virtual size_t size();

private:

    std::shared_ptr<IInput> _base;

    size_t _begin;
    size_t _end;

    std::vector<Frame>::iterator _beginIt;
    std::vector<Frame>::iterator _endIt;

    size_t _size;
};
