/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Camera
*/

#pragma once

#include "input/AInput.hpp"

// The scene's viewport. Never drawn — like Sound, its getMesh() is always empty
// — but it is a real input in the stack, which is the whole point: a pan is a
// Position claim and a zoom a Scale claim, so `camera.moveTo(...)` reaches C++
// through the same per-frame machinery as any shape's own position, with no
// second channel to keep in step.
//
// Core turns its Metadata into the one Camera2D the vertex stage applies to
// every unpinned mesh of that frame.
class Camera final : public AInput
{
public:

    Camera(json::object_t&& args)
        : AInput(std::move(args))
    {
    }

    ~Camera() override = default;

    Mesh getMesh(const Metadata&, const Config&) override { return {}; }
};

// Metadata::position is where the camera LOOKS, in the pixel encoding every
// input's position already uses (screenOffset + world * ratio, y down). So the
// frame centre is screenOffset, which divides out to NDC 0 — the identity a
// scene without a camera has to keep.
//
// Vertices reach the GPU already in NDC (MeshFactory::toNdcPoint), so the
// camera is ndc' = (ndc - centre) * zoom: a magnification about the point it
// looks at. Zoom is Metadata::scale, so `camera.zoom = 2` and `scaleTo(2)` are
// one piece of state.
inline Camera2D cameraFromMetadata(const Metadata& meta)
{
    return {
        meta.position.x / config::screenOffset.x - 1.f,
        meta.position.y / config::screenOffset.y - 1.f,
        meta.scale.x,
        meta.scale.y,
    };
}
