/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Vertex
*/

#pragma once
#include <vulkan/vulkan.h>

#include <cstdint>
#include <opencv2/core/matx.hpp>
#include <opencv2/core/types.hpp>
#include <string>
#include <vector>

#include "Vertex.hpp"

// A fragment shader effect active on a mesh at a given frame.
// name   = shader class name ("Blur", "Grayscale", …)
// params = ordered float values from the shader's args (shaderParams())
// needsBBox / groupParamIndex mirror the IFragmentShader declarations —
// carried here because by the time resolveEffectParams() runs, only this
// struct (not the shader instance) travels with the mesh.
struct ActiveEffect
{
    std::string        name;
    std::vector<float> params;
    bool               needsBBox = false;
    int                groupParamIndex = -1;
    // A single string arg read directly off the effect's JSON (not the numeric
    // p[] path — a string can't ride push constants). Populated only for
    // effects that carry a "filepath" arg (currently just `lut`), where it is
    // the .cube path used as a cache key for a lazily-built, persistently-cached
    // LUT atlas texture in the renderers. Empty for every other effect.
    std::string        strParam;
};

struct Mesh
{
    std::vector<Vertex>       vertices;
    std::vector<uint32_t>     indices;
    bool                      hasTexture = false;
    VkDescriptorSet           textureDescriptor = nullptr;
    std::vector<ActiveEffect> effects;
    int                       zIndex = 0;    // render order — see Metadata::zIndex
    int                       zOrderSeq = 0; // tiebreak for equal zIndex — see Metadata::zOrderSeq
    int                       blendMode = 0; // compositing mode — see Metadata::blendMode / BlendModes.hpp

    // Which _inputs[] slot produced this mesh. Mesh-vector position ≠ input
    // index once hidden/opacity-0 inputs are filtered and the zIndex sort runs,
    // so a matte consumer needs this to find its matte-source mesh by identity.
    int                       inputIndex = -1;
    // Copied from Metadata::matteSource: the input index whose alpha masks this
    // mesh, or -1 for none. Both a matte consumer (this >= 0) and any mesh
    // referenced as a source get isolated into an EffectResultSlot; a 2-sampler
    // combine pass then masks the consumer — see the renderers' matte phase.
    int                       matteSourceInputIndex = -1;
    // Copied from Metadata::isAdjustmentLayer. When true this mesh is never
    // drawn directly; instead the renderer flattens every mesh below it in
    // z-order and runs this mesh's `effects` chain over that composite. See the
    // adjustment-layer flatten passes in both renderers.
    bool                      isAdjustmentLayer = false;
};
