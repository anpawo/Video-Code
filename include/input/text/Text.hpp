/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#pragma once

#include "input/AInput.hpp"

class Text final : public AInput
{
public:

    Text(json::object_t &&args);
    ~Text() = default;
};
