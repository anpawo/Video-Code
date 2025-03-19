/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Iterable
*/

#pragma once

#include <nlohmann/json.hpp>

#include "input/IInput.hpp"

using json = nlohmann::json;

class IterableInput
{
public:

    IterableInput(std::shared_ptr<IInput> input, json startTime, json endTime, int framerate)
        : _input(input)
    {
        ///< The start and end of time are floats, they represent seconds.

        ///< Start/Begin Index
        if (startTime.is_null()) {
            _beginIndex = 0;
        }
        else if (startTime < 0.0f) {
            _beginIndex = startTime.get<float>() * framerate + static_cast<int>(input->size());
        }
        else {
            _beginIndex = startTime.get<float>() * framerate;
        }

        ///< End Index
        if (endTime.is_null()) {
            _endIndex = input->size();
        }
        else if (endTime < 0.0f) {
            _endIndex = endTime.get<float>() * framerate + static_cast<int>(input->size());
        }
        else {
            _endIndex = endTime.get<float>() * framerate;
        }

        _nbFrames = _endIndex - _beginIndex;

        _beginIterator = input->begin() + _beginIndex;
        _endIterator = input->begin() + _endIndex;
    }

    ~IterableInput() = default;

    std::vector<Frame>::iterator begin() { return _beginIterator; }

    std::vector<Frame>::iterator end() { return _endIterator; }

    IInput* get() { return _input.get(); }

    size_t _nbFrames;

private:

    std::shared_ptr<IInput> _input;

    size_t _beginIndex;
    size_t _endIndex;

    ///< Different begin and start than the size of the frames of the input
    std::vector<Frame>::iterator _beginIterator;
    std::vector<Frame>::iterator _endIterator;
};
