/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** ScreenSize
*/

#pragma once

#include <argparse/argparse.hpp>

#include "core/Config.hpp"

namespace VC
{
    ///< Build the render Config. The resolution comes from --width/--height
    ///< (1920x1080 by default) and from nothing else — a scene cannot change
    ///< it, so the world box, the preview surface and the encoder agree by
    ///< construction rather than by negotiation.
    Config makeConfig(const argparse::ArgumentParser &parser);

    ///< Point the world->pixel transform (config::screen / config::screenOffset)
    ///< and Python's VC_SCREEN at a resolution. Called by makeConfig; only worth
    ///< calling directly when a Config is built by hand, as in VisualTest.
    void applyScreenSize(float width, float height);
}
