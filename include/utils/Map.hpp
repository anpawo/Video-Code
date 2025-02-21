/*
** EPITECH PROJECT, 2024
** Utils
** File description:
** DisplayVector
*/

#pragma once

#include <iostream>
#include <map>
#include <ostream>

template <typename K, typename V>
std::ostream &operator<<(std::ostream &os, const std::map<K, V> &map)
{
    os << "{\n\t";
    for (auto it = map.begin(); it != map.end(); it++)
    {
        os << (*it).first;
        os << " = ";
        os << (*it).second;
        if (std::next(it) != map.end())
        {
            os << ",\n\t";
        }
    }
    os << "\n}";
    return os;
}
