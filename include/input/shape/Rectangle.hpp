/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Rectangle
*/

#pragma once

#include "input/shape/BezierPath.hpp"

class Rectangle final : public BezierPath
{
public:

    explicit Rectangle(json::object_t&& args);
    ~Rectangle() override = default;

protected:

    void buildPath(const json::object_t& args) override;
};
