/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/concrete/ABCConcreteInput.hpp"

#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>
#include <utility>

#include "input/IInput.hpp"
#include "utils/Debug.hpp"

ABCConcreteInput::ABCConcreteInput(std::vector<cv::Mat>&& frames)
    : _frames(std::move(frames))
{
}

IInput* ABCConcreteInput::copy()
{
    ABCConcreteInput* cp = new ABCConcreteInput();

    VC_LOG_DEBUG("fully cloned")
    for (const cv::Mat& frame : _frames)
    {
        cp->_frames.push_back(frame.clone());
    }

    return cp;
}

std::vector<cv::Mat>::iterator ABCConcreteInput::begin()
{
    return _frames.begin();
}

std::vector<cv::Mat>::iterator ABCConcreteInput::end()
{
    return _frames.end();
}

size_t ABCConcreteInput::size()
{
    return _frames.size();
}
