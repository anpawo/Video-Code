/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Frame
*/

#pragma once

#include "opencv2/core/mat.hpp"

struct Metadata
{
    int x{0};
    int y{0};
    int rotation{0};
};

struct Frame
{
    Frame(cv::Mat&& mat)
        : _mat(mat) {}

    Frame(cv::Mat&& mat, Metadata meta)
        : _mat(mat), _meta(meta) {}

    ~Frame() = default;

    Frame clone() const
    {
        return Frame(_mat.clone(), _meta);
    }

    cv::Mat _mat;
    Metadata _meta;
};
