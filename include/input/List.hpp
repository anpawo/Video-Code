/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** List
*/

#pragma once

#include <memory>

#include "input/_AInput.hpp"
#include "input/_IInput.hpp"

class List : public _AInput {
public:

    List(std::shared_ptr<_IInput> frames, int n);
    ~List() = default;

private:
};
