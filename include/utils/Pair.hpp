/*
** EPITECH PROJECT, 2024
** Utils
** File description:
** DisplayVector
*/

#pragma once

#include <iostream>
#include <ostream>
#include <utility>

template <typename T1, typename T2>
std::ostream &operator<<(std::ostream &os, const std::pair<T1, T2> &p)
{
    os << "[";
    os << p.first;
    os << ", ";
    os << p.second;
    os << "]";
    return os;
}
