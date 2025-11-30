/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <memory>
#include <set>
#include <vector>

#include "input/Frame.hpp"
#include "input/IInput.hpp"

class AInput : public IInput
{
public:

    AInput(json::object_t&& args, std::set<std::string_view>&& triggers = {});
    virtual ~AInput() = default;

    void flushTransformation() override;

    void apply(const std::string& name, const json::object_t& args) override;

    void construct() override;
    void setBase(cv::Mat&& mat) override;
    void resetCurrentFrameToBase() override;

    void addTransformation(size_t index, bool persistent, std::string&& name, std::function<void(Frame&)>&& f) override;
    void addPersistent(std::string& name, std::function<void(Frame&)>& f) override;
    void addSetter(size_t index, std::vector<std::string>&& name, std::function<void(json::object_t&, Metadata&)>&& f) override;

    Frame& generateNextFrame() override;
    Frame& getCurrentFrame() override;

    void applySetters() override;
    void applyPersistents() override;
    void applyTransformations() override;

    void overlayLastFrame(cv::Mat& background, const v2i& camera) override;

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

    ///< Setters affecting the base from the current frame and onward.
    std::vector<std::vector<std::pair<std::vector<std::string>, std::function<void(json::object_t&, Metadata&)>>>> _setters;

    ///< Transformations staying on every Frame | You remove it if it returns true or if it's in _transformations (scale == 1 --> you dont need it)
    std::vector<std::pair<std::string, std::function<void(Frame&)>>> _persistents;

    ///< Transformation that should affect the current frame. | if the pair 1 is true and the transformation returns true, it will be added to persistent
    std::vector<std::vector<std::tuple<bool, std::string, std::function<void(Frame&)>>>> _transformations;

    ///< Last generated frame in case we do not need to re-generate it.
    std::unique_ptr<Frame> _currentFrame{nullptr};

    ///< Did the Input change ? (The frame of the video advanced)
    bool _frameHasChanged{true};

    ///< Args that need a reconstruct
    std::set<std::string_view> _triggers = {};

    ///< An argument changed
    bool _constructNeeded{false};
};
