/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Input
*/

#pragma once

#include <string>
#include <vector>

#include "input/_IInput.hpp"
#include "opencv2/core/mat.hpp"

class _AInput : public _IInput {
public:

    _AInput(std::string&& inputName, std::vector<cv::Mat>&& frames);
    virtual ~_AInput() = default;

    const std::vector<cv::Mat>& getFrames() final;

    virtual std::vector<cv::Mat> loadFrames(const std::string&);

private:

    /**
     * @ name of the input file
     */
    std::string _inputName{};

    /**
     * @ frames of the input
     * - a single frame for an image
     * - a list of frame for a video
     */
    std::vector<cv::Mat> _frames{};
};
