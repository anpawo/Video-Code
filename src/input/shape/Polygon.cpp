/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Polygon
*/

#include "input/shape/Polygon.hpp"

Polygon::Polygon(json::object_t&& args)
    : BezierPath(std::move(args))
{
}
