/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** ShaderSpace
*/

#pragma once

#include <array>
#include <string>

// A screen-space box: uMin, vMin, uMax, vMax, in absolute frame UV. The thing
// a ShaderSpace names — every mode below is just a different choice of one.
using ShaderBox = std::array<float, 4>;

// Which box a math-shader paint measures its origin and its unit against —
// the C++ side of Python's `Space` enum (videocode/constants.py).
//
// It rides ActiveEffect rather than the alphabetical p[]: a math shader must
// find its own args at a fixed index whatever anchoring it was given, and the
// GLSL never learns the mode anyway — resolveEffectParams has already turned
// it into a resolved origin + unit by the time the push constants are built.
//
// The repo names this concept for the first time here. It was previously
// implemented three times under three names (needsBBox, groupParamIndex,
// UVMapping) — Frame/Shape/Group are those same spaces, now spelled once.
enum class ShaderSpace : int {
    NotMath = -1, ///< Not a math-shader paint — leave the params alone.
    Shape = 0,    ///< The host mesh's own box, this frame. Nothing swims.
    Frame = 1,    ///< The whole frame: the host is a window onto the pattern.
    Anchor = 2,   ///< The host's box re-derived at Metadata::fillShaderSince.
    Group = 3,    ///< The union of every host sharing this paint's group id.
};

inline ShaderSpace shaderSpaceFromString(const std::string &name)
{
    if (name == "frame")
        return ShaderSpace::Frame;
    if (name == "anchor")
        return ShaderSpace::Anchor;
    if (name == "group")
        return ShaderSpace::Group;
    return ShaderSpace::Shape; // the default, and the fallback for junk
}
