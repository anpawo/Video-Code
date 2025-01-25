/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** String
*/

#pragma once

#include <string>

inline std::string operator+(const std::string &str, int number)
{
    return str + std::to_string(number);
}

inline std::string operator+(int number, const std::string &str)
{
    return std::to_string(number) + str;
}
