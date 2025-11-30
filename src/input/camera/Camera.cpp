/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/camera/Camera.hpp"

#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>
#include <utility>

#include "utils/Debug.hpp"
#include "utils/Vector.hpp"

Camera::Camera(cv::Mat&& mat, json::object_t&& args)
    : AInput(std::move(args))
{
    setBase(std::move(mat));
}

void Camera::applySetters()
{
    if (_transformationIndex == _transformations.size()) {
        return;
    }
    for (const auto& [names, t] : _setters[_transformationIndex]) {
        VC_LOG_DEBUG("applySetter: " << names);

        t(getArgs(), getCurrentFrame().meta);

        for (const auto& n : names) {
            if (_triggers.contains(n)) {
                _constructNeeded = true;
                break;
            }
        }
    }
    if (_constructNeeded) {
        _constructNeeded = false;
        ///< Update shape or remove a transformation.
        construct();
    }
}

Frame& Camera::generateNextFrame() // TODO: find a better way than overriding to just remove a line
{
    if (_transformationIndex == _transformations.size()) {
        _frameHasChanged = false;
        return getCurrentFrame();
    }
    _frameHasChanged = true;

    applyPersistents();
    applyTransformations();

    _transformationIndex += 1;
    return getCurrentFrame();
}
