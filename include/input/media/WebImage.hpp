/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#pragma once

#include "input/AInput.hpp"

class WebImage final : public AInput
{
public:

    WebImage(json::object_t &&args);
    ~WebImage() = default;

    void construct() final;
};
