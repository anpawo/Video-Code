/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Video
*/

#pragma once

#include "input/concrete/ABCConcreteInput.hpp"

class Video final : public ABCConcreteInput
{
public:

    Video(const std::string& inputName);
    ~Video() = default;
};
