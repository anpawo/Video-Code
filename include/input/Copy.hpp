/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Copy
*/

#pragma once

#include <memory>

#include "input/_AInput.hpp"
#include "input/_IInput.hpp"

class Copy : public _AInput {
public:

    Copy(std::shared_ptr<_IInput> input);
    ~Copy() = default;

private:
};
