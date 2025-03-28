/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Text
*/

#pragma once

#include "input/concrete/ABCConcreteInput.hpp"

class Text final : public ABCConcreteInput
{
public:

    Text(json::object_t &&args);
    ~Text() = default;
};
