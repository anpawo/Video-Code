/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/camera/Camera.hpp"

#include <algorithm>
#include <functional>
#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>
#include <utility>

Camera::Camera(cv::Mat&& mat, json::object_t&& args)
    : AInput(std::move(args))
{
    setBase(std::move(mat));
}

void Camera::reset()
{
    ///< Keep the metadata if existing
    if (_lastFrame) {
        _lastFrame = std::make_unique<Frame>(_base.clone(), _lastFrame->meta);
    } else {
        _lastFrame = std::make_unique<Frame>(_base.clone());
    }
}

const v2i& Camera::getPosition()
{
    if (_transformationIndex == _transformations.size()) {
        return _lastFrame->meta.position;
    }

    auto& v = _setters[_transformationIndex];
    auto it = v.begin();

    ///< Remove all setPosition
    while (it != v.end()) {
        it = std::find_if(v.begin(), v.end(), [](auto& p) {
            return p.first == "setPosition";
        });

        if (it != v.end()) {
            it->second(getArgs(), getLastFrame().meta);
            v.erase(it);
        }
    }

    return _lastFrame->meta.position;
}
