/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Group
*/

#include "input/composition/Group.hpp"

#include <utility>
#include <vector>

#include "utils/Exception.hpp"

Group::Group(std::vector<std::shared_ptr<IInput>> &inputs, json::object_t &&args)
    : AInput(std::move(args))
{
    const std::vector<size_t> &inputsIndex = _args.at("inputs");

    for (size_t i : inputsIndex) {
        _inputs.push_back(inputs[i]);
    }
}

void Group::generateNextFrame()
{
    throw Error("Group: generateNextFrame: Should never be called.");
}

void Group::overlayLastFrame(cv::Mat &background)
{
    bool anyInputChanged = false;

    for (const auto &input : _inputs) {
        input->overlayLastFrame(background);

        anyInputChanged |= input->hasChanged();
    }

    _hasChanged = anyInputChanged;
}
