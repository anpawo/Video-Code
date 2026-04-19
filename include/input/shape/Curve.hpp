/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Curve
*/

#pragma once

#include "input/AInput.hpp"

// Open curve rendered as a stroke-only quadratic bezier path.
// Points are provided pre-scaled (screen pixels) as [[x,y], ...].
// N-1 straight-line quadratic bezier segments are built from the N sample points.

class Curve : public AInput
{
public:

    Curve(json::object_t&& args);
    ~Curve() override = default;

    Mesh getMesh(const Metadata& meta, const Config& config) override;
};
