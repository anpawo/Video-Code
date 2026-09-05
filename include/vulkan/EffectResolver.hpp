/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** EffectResolver
*/

#pragma once

#include <algorithm>
#include <array>
#include <map>
#include <vector>

#include "input/Metadata.hpp" // config::screen
#include "vulkan/Mesh.hpp"

namespace VC
{
    // Resolve object-space effect params into absolute frame UVs — the ONE
    // place geometry-dependent shader params are patched. Shared by the
    // headless renderer and the preview widget (which used to carry
    // duplicated, name-matched copies of this logic).
    //
    // The Python API speaks in object-relative terms ("crop 20% off the
    // left", "darken toward the corners"), but the GLSL effect pass runs as a
    // fullscreen quad over the input's isolated layer and only sees absolute
    // frame UVs. The object's box depends on per-frame animation state that
    // exists only once the mesh vertices do — so the conversion has to happen
    // here, right after mesh generation, and nowhere else.
    //
    // Driven by the IFragmentShader declarations carried on ActiveEffect:
    //  - needsBBox: prepend the mesh's own screen-space bounding box
    //    (uMin, vMin, uMax, vMax) — the GLSL reads it as p[0..3].
    //  - groupParamIndex >= 0: params[i] is a group id; every mesh sharing
    //    the id gets the UNION of their boxes prepended (and the id removed).
    //    Two-phase by necessity: the union isn't known until every mesh of
    //    the frame has been seen.
    //  - space != NotMath: a math-shader paint. Its 3-float head (the raw
    //    origin request) is REPLACED in place by the resolved origin and unit,
    //    both derived from the one box `space` selects — see resolveMathHead.

    // A mesh's screen-space AABB (NDC → UV): uMin, vMin, uMax, vMax. Also used
    // by Core to derive a PAST frame's box for ShaderSpace::Anchor, which is
    // why it lives here rather than inside the resolve loop.
    inline ShaderBox meshBoxUV(const Mesh& mesh)
    {
        float ndcMinX = 1.f, ndcMinY = 1.f, ndcMaxX = -1.f, ndcMaxY = -1.f;
        for (const auto& v : mesh.vertices) {
            ndcMinX = std::min(ndcMinX, v.pos[0]);
            ndcMaxX = std::max(ndcMaxX, v.pos[0]);
            ndcMinY = std::min(ndcMinY, v.pos[1]);
            ndcMaxY = std::max(ndcMaxY, v.pos[1]);
        }
        // The vertex stage applies the camera AFTER these coordinates, and the
        // effect pass that reads this box runs as a fullscreen quad over the
        // layer that came out — so the box has to make the same journey, or a
        // zoom leaves a crop cutting where the shape used to be. The transform
        // is axis-aligned, so the two corners are the whole of it; min/max
        // again because a mirrored zoom (a negative scale) swaps them.
        const Camera2D& cam = mesh.camera;
        const float     x0 = (ndcMinX - cam.centreX) * cam.zoomX;
        const float     x1 = (ndcMaxX - cam.centreX) * cam.zoomX;
        const float     y0 = (ndcMinY - cam.centreY) * cam.zoomY;
        const float     y1 = (ndcMaxY - cam.centreY) * cam.zoomY;

        return {
            (std::min(x0, x1) + 1.f) / 2.f,
            (std::min(y0, y1) + 1.f) / 2.f,
            (std::max(x0, x1) + 1.f) / 2.f,
            (std::max(y0, y1) + 1.f) / 2.f,
        };
    }

    // A math shader's head, resolved against `box` (uMin, vMin, uMax, vMax in
    // absolute frame UV): params[0..2] go from (originX, originY, originUnit)
    // to (originU, originV, unit).
    //
    // Origin and unit MUST come from the same box — that is the whole anti-swim
    // property. Deriving the origin from a box that follows the host while the
    // pattern's scale stayed frame-sized is what made a growing shape resample
    // its pattern instead of magnifying it.
    inline void resolveMathHead(ActiveEffect& eff, const ShaderBox& box)
    {
        if (eff.params.size() < 3)
            return;

        const float boxW = box[2] - box[0];
        const float boxH = box[3] - box[1];
        const bool  pixels = eff.params[2] > 0.5f;

        // A pixel origin is divided by the OUTPUT resolution, never by whatever
        // surface a given renderer happens to draw into. The preview swapchain
        // is windowRatio-scaled (and DPR-scaled on retina), so measuring against
        // it put a pixel-specified origin in a different place in the preview
        // than in the export — the one thing --width/--height exists to prevent.
        // config::screen is the single answer both renderers already share; it
        // is deliberately NOT a parameter, so no caller can pass its own.
        const float frameW = std::max(config::screen.w(), 1.f);
        const float frameH = std::max(config::screen.h(), 1.f);

        const float originU = pixels
                                  ? box[0] + eff.params[0] / frameW
                                  : box[0] + eff.params[0] * 0.01f * boxW;
        const float originV = pixels
                                  ? box[1] + eff.params[1] / frameH
                                  : box[1] + eff.params[1] * 0.01f * boxH;

        eff.params[0] = originU;
        eff.params[1] = originV;
        // Half the box's height: distances divided by it run -1..1 across the
        // host. Guarded only against degeneracy (a zero-height or inverted box
        // would send the pattern to infinity) — NOT clamped to the frame, so a
        // host that is half off-screen keeps a stable pattern as it slides in.
        eff.params[2] = std::max(boxH * 0.5f, 1e-6f);
    }

    inline void resolveEffectParams(std::vector<Mesh>& meshes)
    {
        struct PendingGroup
        {
            size_t meshIdx;
            size_t effIdx;
            float  group;
        };

        std::vector<PendingGroup>  pending;
        std::map<float, ShaderBox> groupBox;
        // Math paints in ShaderSpace::Group need the same two-phase union, but
        // keyed on ActiveEffect::groupId instead of a param slot — and the id
        // is never erased, because it was never in params to begin with.
        std::vector<PendingGroup>  pendingMath;
        std::map<float, ShaderBox> mathGroupBox;

        for (size_t mi = 0; mi < meshes.size(); ++mi) {
            auto& mesh = meshes[mi];
            if (mesh.effects.empty() || mesh.vertices.empty())
                continue;

            const auto  box = meshBoxUV(mesh);
            const float uMin = box[0], vMin = box[1], uMax = box[2], vMax = box[3];

            for (size_t ei = 0; ei < mesh.effects.size(); ++ei) {
                auto& eff = mesh.effects[ei];

                if (eff.space != ShaderSpace::NotMath) {
                    switch (eff.space) {
                        case ShaderSpace::Shape:
                            resolveMathHead(eff, {uMin, vMin, uMax, vMax});
                            break;
                        case ShaderSpace::Frame:
                            resolveMathHead(eff, {0.f, 0.f, 1.f, 1.f});
                            break;
                        case ShaderSpace::Anchor:
                            // Re-derived by Core from Metadata::fillShaderSince —
                            // a pure function of a declared frame, not a memo of
                            // whatever box this renderer happened to see first.
                            resolveMathHead(eff, eff.anchorBox);
                            break;
                        case ShaderSpace::Group: {
                            pendingMath.push_back({mi, ei, eff.groupId});
                            auto it = mathGroupBox.find(eff.groupId);
                            if (it == mathGroupBox.end()) {
                                mathGroupBox[eff.groupId] = {uMin, vMin, uMax, vMax};
                            } else {
                                it->second[0] = std::min(it->second[0], uMin);
                                it->second[1] = std::min(it->second[1], vMin);
                                it->second[2] = std::max(it->second[2], uMax);
                                it->second[3] = std::max(it->second[3], vMax);
                            }
                            break;
                        }
                        case ShaderSpace::NotMath:
                            break;
                    }
                } else if (eff.groupParamIndex >= 0 && static_cast<size_t>(eff.groupParamIndex) < eff.params.size()) {
                    // Defer: collect this mesh's box into the group union now,
                    // patch the params once every mesh has been seen.
                    const float group = eff.params[eff.groupParamIndex];
                    pending.push_back({mi, ei, group});
                    auto it = groupBox.find(group);
                    if (it == groupBox.end()) {
                        groupBox[group] = {uMin, vMin, uMax, vMax};
                    } else {
                        it->second[0] = std::min(it->second[0], uMin);
                        it->second[1] = std::min(it->second[1], vMin);
                        it->second[2] = std::max(it->second[2], uMax);
                        it->second[3] = std::max(it->second[3], vMax);
                    }
                } else if (eff.needsBBox) {
                    eff.params.insert(eff.params.begin(), {uMin, vMin, uMax, vMax});
                }
            }
        }

        // Second phase: [.., group, ..] → [union bounds(4), .. (group removed) ..]
        for (const auto& pg : pending) {
            auto&       eff = meshes[pg.meshIdx].effects[pg.effIdx];
            const auto& box = groupBox[pg.group];
            eff.params.erase(eff.params.begin() + eff.groupParamIndex);
            eff.params.insert(eff.params.begin(), box.begin(), box.end());
        }

        // Same, for the math paints: one pattern over the union of every host
        // sharing the id — a whole Text under one nebula instead of one per
        // letter. The head stays 3 floats; only the box it resolves against
        // grew.
        for (const auto& pg : pendingMath)
            resolveMathHead(meshes[pg.meshIdx].effects[pg.effIdx], mathGroupBox[pg.group]);
    }
} // namespace VC
