/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Frame
*/

#pragma once

#include <map>
#include <nlohmann/json.hpp>
#include <string>

using json = nlohmann::json;

#include "opencv2/core/mat.hpp"

template <typename T>
struct v2
{
    v2(T x, T y)
        : x(x)
        , y(y)
    {
    }

    T x;
    T y;
};

using v2i = v2<int>;
using v2f = v2<float>;

const std::map<std::string, float> alignRatio = {
    {"right", 0},
    {"bottom", 0},
    {"center", -0.5},
    {"left", -1},
    {"top", -1}
};

struct Metadata
{
    ///< Position
    v2i position{0, 0};

    ///< Align
    v2f align{alignRatio.at("center"), alignRatio.at("center")};

    ///< Rotation
    int rotation{0};
};

struct Transformation
{
    std::string name;
    json::object_t args;
};

struct Frame

{
    Frame(cv::Mat&& mat)
        : mat(mat) {}

    Frame(cv::Mat&& mat, Metadata meta)
        : mat(mat), meta(meta) {}

    ~Frame() = default;

    Frame clone() const
    {
        return Frame(mat.clone(), meta);
    }

    cv::Mat mat;
    Metadata meta;
    // std::vector<Transformation> transformations;
};
