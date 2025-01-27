/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Exception
*/

#pragma once

#include <exception>
#include <string>

class Error : public std::exception {
public:

    Error(const std::string errorMessage)
        : _errorMessage("Error: " + errorMessage) {}

    ~Error() = default;

    const char *what() const noexcept override { return _errorMessage.c_str(); };

private:

    const std::string _errorMessage;
};
