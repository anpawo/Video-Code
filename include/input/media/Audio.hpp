/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Audio
*/

#pragma once

#include <string>

#include "input/AInput.hpp"

class Audio final : public AInput
{
public:

    Audio(json::object_t&& args);
    ~Audio() = default;

    cv::Mat getBaseMatrix(const json::object_t& args);
    void overlay(cv::Mat& bg, size_t index);

    std::string _filepath;
    double _volume{1.0};
    double _startSec{0.0};
};
