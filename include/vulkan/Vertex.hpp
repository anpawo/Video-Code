/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Vertex
*/

#pragma once

struct Vertex
{
    float pos[2];
    float uv[2];    // mode 1: Loop-Blinn coords  mode 2: (dist_to_aaw, half_width_to_aaw)
    float color[4];
    float extra[4]; // [0] draw mode — 0=solid fill, 1=bezier cap, 2=stroke
};
