/*
** EPITECH PROJECT, 2024
** Utils
** File description:
** DisplayVector
*/

#pragma once

#include <algorithm>
#include <iostream>
#include <ostream>
#include <vector>

#include "Utils/Exception.hpp"

template <typename T>
std::ostream &operator<<(std::ostream &os, const std::vector<T> &vec)
{
    os << "[";
    for (auto it = vec.begin(); it != vec.end(); it++) {
        os << *it;
        if (it != vec.end() - 1) {
            os << ", ";
        }
    }
    os << "]";
    return os;
}

template <typename VecType, typename ValType>
inline std::size_t findIndexOrThrow(const std::vector<VecType> &vec, const ValType &value)
{
    auto it = std::find(vec.begin(), vec.end(), value);

    if (it != vec.end()) {
        return std::distance(vec.begin(), it);
    } else {
        throw Error("Couldn't find the requested value");
    }
}

template <typename VecType, typename ValType>
inline bool findOrThrow(const std::vector<VecType> &vec, const ValType &value)
{
    auto it = std::find(vec.begin(), vec.end(), value);

    if (it != vec.end()) {
        return true;
    } else {
        throw Error("Couldn't find the requested value");
    }
}
