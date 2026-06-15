/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Frame
*/

#pragma once

#include <cstdint>
#include <memory>
#include <nlohmann/json.hpp>
#include <opencv2/core/matx.hpp>
#include <ostream>
#include <vector>

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

// Parses a "points" JSON value ([[x,y], [x,y], ...]) into pixel-space anchor-handle
// points (world->pixel ratio + Y-flip applied). Shared by AInput's construction-time
// extraction and the "Args" VertexShader's points mutation, so json::object_t never
// carries the (potentially large, ~600 points for letter glyphs) points array — keeping
// COW clones of Metadata::args() cheap.
inline std::shared_ptr<const std::vector<cv::Vec2f>> parsePointsJson(const json& value)
{
    auto raw = value.get<std::vector<std::vector<float>>>();
    auto points = std::make_shared<std::vector<cv::Vec2f>>();
    points->reserve(raw.size());
    for (const auto& p : raw)
        points->push_back({p[0] * config::worldToPixelRatio, -p[1] * config::worldToPixelRatio});
    return points;
}

// Parses a "contourSizes" JSON value ([n0, n1, ...]) — see parsePointsJson.
inline std::shared_ptr<const std::vector<size_t>> parseContourSizesJson(const json& value)
{
    auto sizes = std::make_shared<std::vector<size_t>>();
    sizes->reserve(value.size());
    for (const auto& s : value)
        sizes->push_back(s.get<size_t>());
    return sizes;
}

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

    // Playback frame index (the render index after Wait remapping). Only Video
    // consumes it; kept out of args so copying a Metadata never touches JSON.
    size_t frameIndex{0};

    // Args for the base matrix of the input. Shared copy-on-write: copying a
    // Metadata only bumps a refcount — for letter glyphs the underlying object
    // holds a ~600-point outline, and a deep copy per frame was the renderer's
    // single biggest CPU cost. Only the "Args" VertexShader clones-then-mutates
    // (see getMetadataFromArgs).
    std::shared_ptr<const json::object_t> argsPtr;

    // Polygon point data (anchor-handle pairs, pixel-space, world->pixel + Y-flip
    // already applied) and per-contour sizes, kept out of argsPtr's json::object_t for
    // the same COW reason — letter glyphs carry ~600 points, and text morphing fires
    // the "points"/"contourSizes" Args VertexShader every frame. Null for non-Polygon
    // inputs (whose args never had a "points"/"contourSizes" key).
    std::shared_ptr<const std::vector<cv::Vec2f>> pointsPtr;
    std::shared_ptr<const std::vector<size_t>>    contourSizesPtr;

    const json::object_t& args() const
    {
        static const json::object_t empty;
        return argsPtr ? *argsPtr : empty;
    }

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
