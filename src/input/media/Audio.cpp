/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Audio
*/

#include "input/media/Audio.hpp"

#include <utility>

Audio::Audio(json::object_t&& args)
    : AInput(std::move(args))
{
    _filepath = _baseArgs.at("filepath").get<std::string>();

    if (_baseArgs.count("volume")) {
        _volume = _baseArgs.at("volume").get<double>();
    }
}

cv::Mat Audio::getBaseMatrix(const json::object_t& /* args */)
{
    // Audio has no visual representation — return an empty matrix
    return cv::Mat();
}

void Audio::overlay(cv::Mat& /* bg */, size_t /* index */)
{
    // Audio does not render visually — no-op
}
