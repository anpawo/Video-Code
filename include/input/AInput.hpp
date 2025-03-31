/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <functional>
#include <memory>
#include <vector>

#include "input/IInput.hpp"

class AInput : public IInput
{
public:

    AInput(json::object_t&& args);
    virtual ~AInput() = default;

    void addTransformation(std::function<void(Frame&)>&& f) override;

    void generateNextFrame() override;

    const Frame& getLastFrame() override;

    void overlayLastFrame(cv::Mat& background) override;

    bool hasChanged() final;

protected:

    json::object_t _args;

    ///< Frame for the initial Input, before any transformation.
    std::unique_ptr<Frame> _base{nullptr};

    ///< Index of the transformations affecting the base.
    size_t _transformationIndex{0};

    ///< Transformation that should affect the current frame.
    std::vector<std::vector<std::function<void(Frame&)>>> _transformations;

    ///< Last generated frame in case we do not need to re-generate it.
    std::unique_ptr<Frame> _lastFrame{nullptr};

    ///< Did the Input change ?
    bool _hasChanged{true};
};
