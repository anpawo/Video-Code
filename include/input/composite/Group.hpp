/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Slice
*/

#pragma once

class Slice
{
public:

    Slice() = default;
    virtual ~Slice() = 0;

    ///< Deep copy of `this`
    IInput* copy() = 0;

    ///< Iteration
    virtual std::vector<cv::Mat>::iterator begin() = 0;
    virtual std::vector<cv::Mat>::iterator end() = 0;

    ///< Size
    virtual size_t size() = 0;

protected:
private:
};
