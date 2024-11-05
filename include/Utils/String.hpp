/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** String
*/

#pragma once

#include <cstddef>
#include <string>

inline std::string operator+(const std::string &str, std::size_t number)
{
    return str + std::to_string(number);
}

inline std::string operator+(std::size_t number, const std::string &str)
{
    return std::to_string(number) + str;
}
