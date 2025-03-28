/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#pragma once

#include "input/concrete/ABCConcreteInput.hpp"

class Image final : public ABCConcreteInput
{
public:

    Image(json::object_t &&args);
    ~Image() = default;
};
