/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Frame
*/

#pragma once

#include <cstdint>
#include <nlohmann/json.hpp>
#include <ostream>

using json = nlohmann::json;

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

    T w() { return x; };

    T h() { return y; };

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
    inline v2f   screen{1920.0f, 1080.0f};
    inline v2f   screenOffset{screen.w() / 2.0f, screen.h() / 2.0f};
    inline float worldToPixelRatio = 120.f;
};

struct Metadata
{
    v2f position{config::screenOffset.x, config::screenOffset.y};
    v2f scale{1.0, 1.0};
    v2f align{0.5, 0.5}; // 0 to 1

    uint8_t opacity{255}; // 0 to 255

    float rotation{0.0};

    // Render order — meshes are stable-sorted by (zIndex, zOrderSeq)
    // ascending before drawing, so lower values render first (further
    // behind). Only meaningful when zIndexExplicit is true; otherwise
    // Core::generateMeshes falls back to the input's creation order, which
    // is what the Python-side default (Metadata.zIndex = self.index) means.
    int zIndex{0};

    // True once a `ZIndex` VertexShader has been applied.
    bool zIndexExplicit{false};

    // Tiebreak for equal zIndex: bumped each time zIndex is explicitly set,
    // so the most recently changed one wins (renders on top).
    int zOrderSeq{0};

    bool hidden{false};

    // True when no "Args" VertexShader has ever fired for this input.
    // BezierPath uses this to skip buildPath on frames 2+ (geometry is stable).
    bool argsStatic{true};

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

        os << std::setw(11) << "zIndex:"
           << m.zIndex << (m.zIndexExplicit ? "" : " (default)") << '\n';

        os << std::setw(11) << "zOrderSeq:"
           << m.zOrderSeq << '\n';

        os << std::setw(11) << "opacity:"
           << (int)(m.opacity) << "\n";

        os << std::setw(11) << "hidden:"
           << std::boolalpha << m.hidden;

        return os;
    }
};
