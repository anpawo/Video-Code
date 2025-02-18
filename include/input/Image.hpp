/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#pragma once

#include "input/ABCInput.hpp"

class Image : public ABCInput
{
public:

    Image(const std::string& inputName);
    ~Image() = default;

private:

    const std::string _inputName{};
};
