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
#include "shader/ShaderSpace.hpp"

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
    std::string strParam;

    // Math-shader paints only (NotMath for every other effect). Which box
    // resolveEffectParams measures the pattern's origin and unit against, and
    // the id ShaderSpace::Group unions on — deliberately NOT in params, so a
    // math shader's own args keep the same p[] index in every mode.
    ShaderSpace space = ShaderSpace::NotMath;
    float       groupId = 0.f;
    // ShaderSpace::Anchor only: the host's box (uMin, vMin, uMax, vMax) at
    // Metadata::fillShaderSince, re-derived by Core — the resolver has no
    // access to the inputs, and the box of a PAST frame isn't in this mesh.
    ShaderBox anchorBox{0.f, 0.f, 1.f, 1.f};
};

// The scene camera, resolved for ONE draw and pushed to the vertex stage as a
// vec4: gl_Position.xy = (ndc - centre) * zoom. Per-draw rather than per-frame
// because a pinToFrame() mesh takes the identity in the middle of a moving
// scene — and so does every composite quad, whose layer already had the camera
// applied when it was drawn.
//
// The default IS the identity, and exactly: (v - 0) * 1 is bit-for-bit v, so a
// scene with no camera renders byte-identically to one built before cameras
// existed.
struct Camera2D
{
    float centreX = 0.f; // where the camera looks, in NDC
    float centreY = 0.f;
    float zoomX = 1.f;
    float zoomY = 1.f;
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
    int inputIndex = -1;
    // Copied from Metadata::matteSource: the input index whose alpha masks this
    // mesh, or -1 for none. Both a matte consumer (this >= 0) and any mesh
    // referenced as a source get isolated into an EffectResultSlot; a 2-sampler
    // combine pass then masks the consumer — see the renderers' matte phase.
    int matteSourceInputIndex = -1;
    // The camera this mesh is drawn through — the scene's, or the identity when
    // Metadata::pinnedToFrame excused it. Resolved by Core (the only place that
    // can see both the camera input and this mesh's own input) so the renderers
    // just push what they are handed.
    Camera2D camera;

    // Copied from Metadata::isAdjustmentLayer. When true this mesh is never
    // drawn directly; instead the renderer flattens every mesh below it in
    // z-order and runs this mesh's `effects` chain over that composite. See the
    // adjustment-layer flatten passes in both renderers.
    bool isAdjustmentLayer = false;

    // Copied from Metadata::isComposition. A composition layer is never drawn itself: the
    // renderer flattens the meshes whose compositionIndex names it into this mesh's
    // EffectResultSlot, grades that with this mesh's `effects`, scales its
    // alpha by compOpacity, and composites the result once at this mesh's
    // z-position. That is what makes a group fade as ONE layer.
    bool isComposition = false;
    // Copied from Metadata::compositionIndex: the INPUT index of the composition layer that
    // owns this mesh, or -1. Resolved to a mesh position through
    // m_inputIndexToMeshPos, exactly like matteSourceInputIndex.
    int compositionIndex = -1;
    // Comp layers only: the layer's own opacity, 0..1 (hidden counts as 0).
    // Applied to the flattened layer as one final pass, so two overlapping
    // members at 50% read as one flat 50% shape instead of a darker patch.
    float compOpacity = 1.f;
};
