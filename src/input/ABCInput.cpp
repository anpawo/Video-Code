/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/ABCInput.hpp"

#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>

#include "input/IInput.hpp"
#include "utils/Debug.hpp"

IInput* ABCInput::copy()
{
    ABCInput* cp = new ABCInput();

    VC_LOG_DEBUG("fully cloned")
    for (const cv::Mat& frame : _frames)
    {
        cp->_frames.push_back(frame.clone());
    }

    return cp;
}

std::vector<cv::Mat>& ABCInput::getFrames()
{
    return _frames;
}

// void _AInput::concat(std::shared_ptr<_IInput> other)
// {
//     _frames.insert(_frames.end(), other->cgetFrames().cbegin(), other->cgetFrames().cend());
// }

// void _AInput::setFrames(std::vector<cv::Mat>&& frames)
// {
//     _frames = std::forward<std::vector<cv::Mat>>(frames);
// }
