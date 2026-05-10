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

    void add(nlohmann::basic_json<>& modification) final;

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

    ///< Arguments needed to generate the Input's matrix
    const json::object_t _baseArgs;

    ///< Effects (Affect the pixels of the Input) | Effects are duplicated over duration
    ///< That't why we have 2 vectors.
    std::vector<std::unique_ptr<IFragmentShader>> _effects{};
    std::vector<std::vector<size_t>>              _effectTimeline{};

    ///< Transformations (Affect the Metadata of the Input)
    std::vector<Metadata> _metas{Metadata{.args = _baseArgs}};
};
