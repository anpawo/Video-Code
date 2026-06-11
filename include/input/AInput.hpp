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
    std::vector<ActiveEffect> getActiveEffectsAtFrame(size_t frame) const;

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
    std::vector<Metadata> _metas{Metadata{.argsPtr = _baseArgsPtr}};
};
