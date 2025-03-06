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

ABCConcreteInput::ABCConcreteInput(std::vector<Frame>&& frames)
    : _frames(std::move(frames))
{
}

IInput* ABCConcreteInput::copy()
{
    ABCConcreteInput* cp = new ABCConcreteInput();

    VC_LOG_DEBUG("fully cloned")
    for (const Frame& frame : _frames)
    {
        cp->_frames.push_back(frame.clone());
    }

    return cp;
}

std::vector<Frame>::iterator ABCConcreteInput::begin()
{
    return _frames.begin();
}

std::vector<Frame>::iterator ABCConcreteInput::end()
{
    return _frames.end();
}

Frame& ABCConcreteInput::back()
{
    return _frames.back();
}

void ABCConcreteInput::repeat(size_t n)
{
    const size_t initialSize = _frames.size();

    while (n--)
    {
        for (size_t i = 0; i < initialSize; i++)
        {
            _frames.push_back(_frames[i].clone());
        }
    }
}

size_t ABCConcreteInput::size()
{
    return _frames.size();
}
