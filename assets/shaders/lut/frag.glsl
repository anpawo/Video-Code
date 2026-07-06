#version 450

// LUT color grade — the THIRD hand-built exception to the effect-chain rule
// "an effect samples one texture and never composites" (glow, matte are the
// first two). It samples TWO textures:
//   contentTex = the input's own isolated layer (the pixels being graded)
//   lutTex     = a persistent 2D atlas of a .cube 3D LUT, built once from a
//                file path and cached across frames (see LutAtlas.hpp).
// Unlike matte, the second texture is not another input — it is a file-keyed
// GPU resource attached to this effect instance. This folder is SKIPPED by the
// generic single-sampler auto-discovery loop; the 2-sampler layout + push
// constants are hand-built by createLutResources() in both renderers.

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D contentTex; // pixels to grade
layout(set = 0, binding = 1) uniform sampler2D lutTex;     // N*N x N LUT atlas

layout(push_constant) uniform PC {
    float texelX;  // unused here (single-pass effect)
    float texelY;  // unused here
    float p[8];    // p[0] = intensity (0=off, 1=full), p[1] = lut size N
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4 src = texture(contentTex, fragUV);
    float intensity = pc.p[0];
    float N = pc.p[1];

    vec3 c = clamp(src.rgb, 0.0, 1.0);

    // Blue axis selects the tile: bIdx in [0, N-1]. Two adjacent tiles (b0, b1)
    // are sampled and mix()-ed by the blue fraction — trilinear via 2 bilinear
    // taps (the sampler's LINEAR filter interpolates R across a tile and G down
    // its rows for free).
    float atlasW = N * N;
    float bIdx = c.b * (N - 1.0);
    float b0 = floor(bIdx);
    float b1 = min(b0 + 1.0, N - 1.0);
    float f = bIdx - b0;

    // Fractional R index within a tile stays in [0, N-1] so the horizontal
    // LINEAR filter never bleeds across the tile boundary. +0.5 hits texel
    // centres; divide by the atlas dimensions to get [0,1] UVs.
    float uR = c.r * (N - 1.0);
    float v = (c.g * (N - 1.0) + 0.5) / N;

    float u0 = (b0 * N + uR + 0.5) / atlasW;
    float u1 = (b1 * N + uR + 0.5) / atlasW;

    vec3 g0 = texture(lutTex, vec2(u0, v)).rgb;
    vec3 g1 = texture(lutTex, vec2(u1, v)).rgb;
    vec3 graded = mix(g0, g1, f);

    // intensity dissolves between the original and the fully-graded colour.
    // Alpha is untouched: the LUT grades colour only, it never re-shapes the
    // input's coverage.
    outColor = vec4(mix(c, graded, intensity), src.a);
}
