/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <functional>

#include "input/Frame.hpp"

class IInput
{
public:

    IInput() = default;
    virtual ~IInput() = default;

    virtual void flushTransformation() = 0;

    virtual void apply(const std::string& name, const json::object_t& args) = 0;

    ///< Construction of the Input; on start and when args change.
    virtual void construct() = 0;
    virtual void setBase(cv::Mat&& mat) = 0;
    virtual void resetCurrentFrameToBase() = 0;

    ///< Add a setter / persistent transformation / transformation
    virtual void addSetter(size_t index, std::vector<std::string>&& name, std::function<void(json::object_t&, Metadata&)>&& f) = 0;
    virtual void addPersistent(std::string& name, std::function<void(Frame&)>& f) = 0;
    virtual void addTransformation(size_t index, bool persistent, std::string&& name, std::function<void(Frame&)>&& f) = 0;

    ///< Generate next frame
    virtual Frame& generateNextFrame() = 0;

    ///< Get the last frame generated
    virtual Frame& getCurrentFrame() = 0;

    ///< Apply the setters / transformations
    virtual void applySetters() = 0;
    virtual void applyPersistents() = 0;
    virtual void applyTransformations() = 0;

    ///< Overlay the last frame generated
    virtual void overlayLastFrame(cv::Mat& background, const v2i& camera) = 0;

    ///< Did the Input change ?
    virtual bool frameHasChanged() = 0;

    ///< Getter
    virtual json::object_t& getArgs() = 0;
};
