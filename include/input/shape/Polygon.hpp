/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Polygon
*/

#pragma once

#include "input/shape/BezierPath.hpp"

class Polygon final : public BezierPath
{
public:

    explicit Polygon(json::object_t&& args);
    ~Polygon() override = default;

protected:

    void buildPath(const json::object_t& args) override;
};
