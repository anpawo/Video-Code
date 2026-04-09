/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Circle
*/

#pragma once

#include "input/shape/BezierPath.hpp"

class Circle final : public BezierPath
{
public:

    Circle(json::object_t&& args);
    ~Circle() override = default;

protected:

    void buildPath(const json::object_t& args) override;
};
