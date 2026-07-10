/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <cstdint>
#include <memory>
#include <nlohmann/json.hpp>
#include <opencv2/core/matx.hpp>
#include <vector>

#include "input/IInput.hpp"
#include "shader/IFragmentShader.hpp"

using json = nlohmann::json;

// Spans (start, n) during which an ambient clock category is paused — built
// by Core from Wait events' `stop` lists (freeze() = a wait stopping all
// three). Scheduled state needs no spans: it holds by itself.
struct ClockStops
{
    std::vector<std::pair<size_t, size_t>> videos;
    std::vector<std::pair<size_t, size_t>> paints;
    std::vector<std::pair<size_t, size_t>> effects;

    // Total paused frames of `spans` strictly before `frame` — subtracting it
    // from a display frame yields the category's clock: constant inside a
    // span (paused), advancing outside (resumes where it stopped, no skip).
    static size_t pausedBefore(const std::vector<std::pair<size_t, size_t>>& spans, size_t frame)
    {
        size_t total = 0;
        for (const auto& [start, n] : spans)
            if (frame > start)
                total += std::min(n, frame - start);
        return total;
    }

    // Paused frames of `spans` between `since` and `frame` — the amount a
    // clock that started counting at `since` has been held.
    static size_t pausedBetween(const std::vector<std::pair<size_t, size_t>>& spans, size_t since, size_t frame)
    {
        return pausedBefore(spans, frame) - pausedBefore(spans, std::min(since, frame));
    }
};

class AInput : public IInput
{
public:

    AInput(json::object_t&& args);
    virtual ~AInput() = default;

    // -

    void add(const std::string& name, const std::string& type, json::object_t&& args) final;

    // -

    // Restores all modification-derived state (metas, effects, timeline) to the
    // freshly-constructed state, keeping _baseArgs (and any subclass resources, e.g.
    // a loaded texture or open video file). Lets hot-reload reuse an input whose
    // Create entry didn't change without re-running its (possibly expensive) constructor.
    void resetModifications();

    // -

    Metadata getMetadata(size_t index) final;

    // -

    // Returns the fragment shader effects active at the given frame index.
    // Empty when no effect is scheduled at that frame.
    std::vector<ActiveEffect> getActiveEffectsAtFrame(size_t frame, const ClockStops& stops) const;

    // -

protected:

    static cv::Vec4b colorFromJson(const json& c, uint8_t opacity)
    {
        return cv::Vec4b(
            c[0].get<uint8_t>(),
            c[1].get<uint8_t>(),
            c[2].get<uint8_t>(),
            static_cast<uint8_t>(c[3].get<uint8_t>() * (opacity / 255.f))
        );
    }

    ///< Initial points/contourSizes popped out of the Create() args (see
    ///< Metadata::pointsPtr/contourSizesPtr) — re-seeded into _metas[0] by
    ///< resetModifications() on hot-reload. Null when args has no such key
    ///< (non-Polygon inputs).
    const std::shared_ptr<const std::vector<cv::Vec2f>> _initialPoints;
    const std::shared_ptr<const std::vector<size_t>>    _initialContourSizes;

    ///< Arguments needed to generate the Input's matrix. The shared_ptr is the
    ///< canonical owner — every Metadata in _metas shares it (copy-on-write);
    ///< _baseArgs is a convenience alias for subclasses.
    const std::shared_ptr<const json::object_t> _baseArgsPtr;
    const json::object_t&                       _baseArgs;

    ///< True once any "Args" VertexShader has been applied to this input.
    ///< Passed through to Metadata.argsStatic so getMesh() can skip buildPath.
    bool _hasArgsShader{false};

    ///< Effects (Affect the pixels of the Input) | Effects are duplicated over duration
    ///< That't why we have 2 vectors.
    std::vector<std::unique_ptr<IFragmentShader>> _effects{};
    std::vector<std::vector<size_t>>              _effectTimeline{};

    ///< Transformations (Affect the Metadata of the Input)
    std::vector<Metadata> _metas{Metadata{
        .argsPtr = _baseArgsPtr,
        .pointsPtr = _initialPoints,
        .contourSizesPtr = _initialContourSizes,
    }};
};
