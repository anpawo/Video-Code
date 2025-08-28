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

#include "input/Frame.hpp"
#include "input/IInput.hpp"

class AInput : public IInput
{
public:

    AInput(json::object_t&& args);
    virtual ~AInput() = default;

    void flushTransformation() override;

    void apply(const std::string& name, const json::object_t& args) override;

    void setBase(cv::Mat&& mat) override;

    void addTransformation(size_t index, std::function<void(Frame&)>&& f) override;

    Frame& generateNextFrame() override;

    Frame& getLastFrame() override;

    void overlayLastFrame(cv::Mat& background) override;

    bool frameHasChanged() final;

protected:

    json::object_t _args;

    ///< Frame for the initial Input, before any transformation.
    cv::Mat _base;

    size_t _flushedTransformationIndex{0};

    ///< Index of the transformations affecting the base.
    size_t _transformationIndex{0};

    ///< Transformation that should affect the current frame.
    std::vector<std::vector<std::function<void(Frame&)>>> _transformations;

    ///< Last generated frame in case we do not need to re-generate it.
    std::unique_ptr<Frame> _lastFrame{nullptr};

    ///< Did the Input change ? (The frame of the video advanced)
    bool _frameHasChanged{true};

    ///< Did the arguments of the Input change ?
    // (Usually for shapes but could be opacity for other stuff)
    bool _argsHaveChanged{true};
};
