/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Register
*/

#include "vm/Register.hpp"

#include <utility>

#include "utils/Debug.hpp"

void Register::updateInstructions(json::array_t&& newInstructions)
{
    _instructions = std::forward<json::array_t>(newInstructions);

    VC_LOG_DEBUG("register uploaded")
}

void Register::runNextInstruction()
{
    _mappedInstructions.at(_instructions[_inputs.size()][0])(_instructions[_inputs.size()][1]);
}

std::shared_ptr<IInput> Register::operator[](size_t index)
{
    while (_inputs.size() <= index)
    {
        runNextInstruction();
    }

    return _inputs[index];
}
