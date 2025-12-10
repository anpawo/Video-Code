/*
** EPITECH PROJECT, 2024
** Utils
** File description:
** DisplayVector
*/

#pragma once

#include <iostream>
#include <ostream>
#include <vector>

template <typename T>
std::ostream &operator<<(std::ostream &os, const std::vector<T> &vec)
{
    os << "[";
    for (const auto &it : vec) {
        os << it;
        os << ", ";
    }
    os << "]";
    return os;
}
