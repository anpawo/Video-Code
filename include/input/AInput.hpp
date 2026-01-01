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

#include "effect/IShader.hpp"
#include "effect/ITransform.hpp"
#include "input/IInput.hpp"
#include "input/Metadata.hpp"

using json = nlohmann::json;

class AInput : public IInput
{
public:

    AInput(json::object_t&& args);
    virtual ~AInput() = default;

    // -

    void add(nlohmann::basic_json<>& modification) final;

    // -

    Metadata getMetadata(int index);

    // -

    void overlay(cv::Mat& bg, size_t index);

    // -

protected:

    ///< Arguments needed to generate the Input's matrix
    const json::object_t _baseArgs;

    ///< Effects (Affect the pixels of the Input)
    std::vector<std::unique_ptr<IShader>> _effects{};
    std::vector<std::vector<size_t>> _effectTimeline{};

    ///< Transformations (Affect the Metadata of the Input)
    std::vector<std::pair<size_t, std::map<Transform, json::object_t>>> _transformations;
};
