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
struct v2
{
    v2(T x, T y)
        : x(x)
        , y(y)
        , w(this->x)
        , h(this->y)
    {
    }

    T x;
    T y;

    T& w;
    T& h;

    friend std::ostream& operator<<(std::ostream& os, const v2& v)
    {
        os << "x:" << v.x << ", y:" << v.y;

        return os;
    }
};

using _v2i = v2<int>;
using v2f = v2<float>;

namespace config
{
    inline v2f screen{1920.0f, 1080.0f};
    inline v2f screenOffset{screen.w / 2.0f, screen.h / 2.0f};
};

struct Metadata
{
    v2f position{config::screenOffset.x, config::screenOffset.y};
    v2f scale{1.0, 1.0};
    v2f align{0.5, 0.5}; // -1 to 1

    float rotation{0.0};

    bool hidden{false};

    json::object_t args; // args for the base matrix of the input

    friend std::ostream& operator<<(std::ostream& os, const Metadata& m)
    {
        os << std::left;

        os << std::setw(11) << "position:"
           << std::setw(3) << m.position.x
           << " x " << m.position.y << '\n';

        os << std::setw(11) << "scale:"
           << std::setw(3) << m.scale.x
           << " x " << m.scale.y << '\n';

        os << std::setw(11) << "align:"
           << std::setw(3) << m.align.x
           << " x " << m.align.y << '\n';

        os << std::setw(11) << "rotation:"
           << m.rotation << "°\n";

        os << std::setw(11) << "hidden:"
           << std::boolalpha << m.hidden;

        return os;
    }
};
