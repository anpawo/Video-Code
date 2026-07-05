/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** BlendModes — per-input compositing blend state (shared by both renderers)
*/

#pragma once
#include <vulkan/vulkan.h>

namespace VC
{
    // Per-input blend modes. The index is carried end to end and must stay in
    // sync across all four layers:
    //   Python `blendMode` VertexShader (resolves the string to this int) →
    //   Metadata::blendMode → Mesh::blendMode → m_pipelines[index].
    //
    //   0 = Normal    standard src-alpha "over"
    //   1 = Multiply  darkens   (out = src*dst)
    //   2 = Screen    lightens  (out = src + dst - src*dst)
    //   3 = Add       linear dodge, clips toward white (out = src + dst)
    //
    // Overlay is deliberately absent: it is a piecewise conditional on the
    // destination luminance, so the fragment shader would have to READ the
    // current framebuffer pixel (subpass input attachment / self-dependency).
    // That is a render-pass restructure, not a blend-state tweak, and cannot be
    // expressed with fixed-function Vulkan blend factors. See docs/ADDING_EFFECTS.md.
    inline constexpr int kBlendModeCount = 4;

    // Both renderers build one pipeline per mode — everything (shader modules,
    // vertex input, layout, viewport/raster/multisample state) is identical
    // except this attachment. Keeping the recipe here (not duplicated in each
    // createPipeline) is the same shared-header discipline as EffectResolver.hpp.
    //
    // Alpha factors are identical across every mode: the mode only changes how
    // RGB combines with the framebuffer; coverage ("over") is unchanged. The
    // color recipes assume straight (non-premultiplied) alpha and are exact for
    // opaque src pixels (srcAlpha=1). At partial alpha (anti-aliased edges) the
    // color modes are a documented v1 approximation — Multiply fades edges to
    // dst, but Screen/Add use the un-premultiplied src color, so their edges do
    // not soften by alpha. Acceptable for the common opaque-compositing case.
    inline VkPipelineColorBlendAttachmentState blendAttachmentFor(int mode)
    {
        VkPipelineColorBlendAttachmentState a{};
        a.blendEnable = VK_TRUE;
        a.colorBlendOp = VK_BLEND_OP_ADD;

        // Standard "over" alpha for all modes.
        a.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
        a.dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
        a.alphaBlendOp = VK_BLEND_OP_ADD;

        a.colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT |
                           VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;

        switch (mode) {
            case 1: // Multiply: src*dst + dst*(1-srcA). srcA=1 → src*dst; srcA=0 → dst (edges fade).
                a.srcColorBlendFactor = VK_BLEND_FACTOR_DST_COLOR;
                a.dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
                break;
            case 2: // Screen: src*1 + dst*(1-src) = src + dst - src*dst (exact for opaque src).
                a.srcColorBlendFactor = VK_BLEND_FACTOR_ONE;
                a.dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_COLOR;
                break;
            case 3: // Add / linear dodge: src + dst, clips to white.
                a.srcColorBlendFactor = VK_BLEND_FACTOR_ONE;
                a.dstColorBlendFactor = VK_BLEND_FACTOR_ONE;
                break;
            case 0: // Normal: MUST stay byte-identical to the pre-blend-mode pipeline (goldens depend on it).
            default:
                a.srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA;
                a.dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
                break;
        }
        return a;
    }

} // namespace VC
