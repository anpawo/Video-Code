/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Frame
*/

#pragma once

#include <nlohmann/json.hpp>
#include <ostream>

using json = nlohmann::json;

template <typename T>
struct _v2
{
    _v2(T x, T y)
        : x(x)
        , y(y)
    {
    }

    T x;
    T y;
};

using _v2i = _v2<int>;
using _v2f = _v2<float>;

struct Metadata
{
    _v2f position{0.0, 0.0};
    _v2f scale{1.0, 1.0};
    _v2f align{0.5, 0.5}; // -1 to 1

    float rotation{0.0};

    bool hidden{false};

    json::object_t args; // args for the base matrix of the input

    friend std::ostream& operator<<(std::ostream& os, const Metadata& m)
    {
        return os << "position: x " << m.position.x << ", y " << m.position.y
                  << "\nscale: x " << m.scale.x << ", y " << m.scale.y
                  << "\nalign: x " << m.align.x << ", y " << m.align.y
                  << "\nrotation: " << m.rotation
                  << "\nhidden: " << m.hidden << std::endl;
    }
};
