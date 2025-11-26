/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

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
    void addSetter(size_t index, std::string&& setterName, std::function<void(json::object_t&, Metadata&)>&& f) override;

    Frame& generateNextFrame() override;

    Frame& getLastFrame() override;

    void applySetters() override;
    void applyTransformations() override;

    void overlayLastFrame(cv::Mat& background, const v2i& camera) override;

    void construct() override;

    bool frameHasChanged() final;

    ///< Getter
    json::object_t& getArgs() final;

protected:

    json::object_t _args;

    ///< Frame for the initial Input, before any transformation.
    cv::Mat _base;

    size_t _flushedTransformationIndex{0};

    ///< Index of the transformations and the setters affecting the base.
    size_t _transformationIndex{0};

    ///< Transformation that should affect the current frame.
    std::vector<std::vector<std::function<void(Frame&)>>> _transformations;

    ///< Setters affecting the base from the current frame and onward.
    std::vector<std::vector<std::pair<std::string, std::function<void(json::object_t&, Metadata&)>>>> _setters;

    ///< Last generated frame in case we do not need to re-generate it.
    std::unique_ptr<Frame> _lastFrame{nullptr}; // TODO: check is _lastFrame is just current frame

    ///< Did the Input change ? (The frame of the video advanced)
    bool _frameHasChanged{true};

    ///< Args that need a reconstruct | Abandonned the idea
    // std::vector<std::string_view> _triggers = {};
};
