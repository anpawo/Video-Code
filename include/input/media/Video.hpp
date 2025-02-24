/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Video
*/

#pragma once

#include "input/ABCInput.hpp"

class Video : public ABCInput
{
public:

    Video(const std::string& inputName);
    ~Video() = default;

private:

    const std::string _inputName{};
};
