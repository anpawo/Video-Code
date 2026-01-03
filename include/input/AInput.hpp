/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <memory>
#include <nlohmann/json.hpp>
#include <opencv2/core/mat.hpp>
#include <vector>

#include "input/IInput.hpp"
#include "input/Metadata.hpp"
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

    Metadata getMetadata(size_t index);

    // -

    void overlay(cv::Mat& bg, size_t index);

    // -

protected:

    ///< Arguments needed to generate the Input's matrix
    const json::object_t _baseArgs;

    ///< Effects (Affect the pixels of the Input) | Effects are duplicated over duration
    ///< That't why we have 2 vectors.
    std::vector<std::unique_ptr<IFragmentShader>> _effects{};
    std::vector<std::vector<size_t>> _effectTimeline{};

    ///< Transformations (Affect the Metadata of the Input)
    std::vector<Metadata> _metas{Metadata{.args = _baseArgs}};
};
