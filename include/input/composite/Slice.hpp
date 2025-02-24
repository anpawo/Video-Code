/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Slice
*/

#pragma once

#include <vector>

#include "input/composite/ABCCompositeInput.hpp"
#include "opencv2/core/mat.hpp"

class Slice final : public ABCCompositeInput
{
public:

    Slice(std::shared_ptr<IInput> input, int begin, int end);
    ~Slice() = default;

    ///< Deep copy of `this`
    IInput* copy();

    ///< Iteration
    virtual std::vector<cv::Mat>::iterator begin();
    virtual std::vector<cv::Mat>::iterator end();

    ///< Size
    virtual size_t size();

private:

    std::shared_ptr<IInput> _base;

    size_t _begin;
    size_t _end;

    std::vector<cv::Mat>::iterator _beginIt;
    std::vector<cv::Mat>::iterator _endIt;

    size_t _size;
};
