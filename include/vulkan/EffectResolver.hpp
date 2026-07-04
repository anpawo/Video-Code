/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** EffectResolver
*/

#pragma once

#include <array>
#include <map>
#include <vector>

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
    inline void resolveEffectParams(std::vector<Mesh>& meshes)
    {
        struct PendingGroup
        {
            size_t meshIdx;
            size_t effIdx;
            float  group;
        };
        std::vector<PendingGroup>             pending;
        std::map<float, std::array<float, 4>> groupBox;

        for (size_t mi = 0; mi < meshes.size(); ++mi) {
            auto& mesh = meshes[mi];
            if (mesh.effects.empty() || mesh.vertices.empty())
                continue;

            // Per-mesh screen-space AABB (NDC → UV).
            float ndcMinX = 1.f, ndcMinY = 1.f, ndcMaxX = -1.f, ndcMaxY = -1.f;
            for (const auto& v : mesh.vertices) {
                ndcMinX = std::min(ndcMinX, v.pos[0]);
                ndcMaxX = std::max(ndcMaxX, v.pos[0]);
                ndcMinY = std::min(ndcMinY, v.pos[1]);
                ndcMaxY = std::max(ndcMaxY, v.pos[1]);
            }
            const float uMin = (ndcMinX + 1.f) / 2.f;
            const float uMax = (ndcMaxX + 1.f) / 2.f;
            const float vMin = (ndcMinY + 1.f) / 2.f;
            const float vMax = (ndcMaxY + 1.f) / 2.f;

            for (size_t ei = 0; ei < mesh.effects.size(); ++ei) {
                auto& eff = mesh.effects[ei];

                if (eff.groupParamIndex >= 0 && static_cast<size_t>(eff.groupParamIndex) < eff.params.size()) {
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
    }
} // namespace VC
