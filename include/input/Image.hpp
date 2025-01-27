/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#pragma once

#include <string>

#include "input/_AInput.hpp"

class Image : public _AInput {
public:

    Image(std::string&& inputName);
    ~Image() = default;

private:

    /**
     * @ name of the input file
     */
    const std::string _inputName{};
};
