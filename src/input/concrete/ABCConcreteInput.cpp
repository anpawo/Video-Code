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

ABCConcreteInput::ABCConcreteInput(json::object_t&& args)
    : _args(std::move(args))
{
}

ABCConcreteInput::ABCConcreteInput(std::vector<Frame>&& frames)
    : _frames(std::move(frames))
{
}

IInput* ABCConcreteInput::copy()
{
    json::object_t args = _args;
    ABCConcreteInput* cp = new ABCConcreteInput(std::move(args));

    for (const Frame& frame : _frames) {
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

    while (n--) {
        for (size_t i = 0; i < initialSize; i++) {
            _frames.push_back(_frames[i].clone());
        }
    }
}

size_t ABCConcreteInput::size()
{
    return _frames.size();
}
