#version 450

layout(location = 0) in vec2 fragUV;
layout(location = 1) in vec4 fragColor;
layout(location = 2) in vec4 fragExtra; // [0] = draw mode

layout(set = 0, binding = 0) uniform UBO {
    float time;
    float pad0; float pad1; float pad2;
    float resX;
    float resY;
    float pixelSize;  // 1.0 / min(screenWidth, screenHeight)
    float pad3;
} ubo;

// Texture sampler for mode 5 (Image input).
// Always bound — non-textured meshes bind a 1×1 white dummy so this is always valid.
layout(set = 1, binding = 0) uniform sampler2D texSampler;

// Modes 3 and 4: shape SDF parameters (hw, hh, r, sw)
layout(push_constant) uniform ShapeParams {
    float hw;  // half-width  (world units)
    float hh;  // half-height (world units)
    float r;   // corner radius (world units)
    float sw;  // stroke half-width (world units)
} shape;

layout(location = 0) out vec4 outColor;

// Signed distance to a rounded rectangle centred at origin.
// b = half-extents, r = corner radius.
float sdRoundedBox(vec2 p, vec2 b, float r) {
    vec2 q = abs(p) - b + r;
    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}

void main() {
    int mode = int(round(fragExtra[0]));

    if (mode == 0) {
        // ── Solid fill triangle ───────────────────────────────────────────
        if (fragColor.a == 0.0) discard;
        outColor = fragColor;

    } else if (mode == 1) {
        // ── Bézier cap (Loop-Blinn) ───────────────────────────────────────
        if (fragColor.a == 0.0) discard;
        float x     = fragUV.x;
        float y     = fragUV.y;
        float Fxy   = y - x * x;
        float w     = fwidth(Fxy);
        float alpha = smoothstep(-w, w, Fxy);
        if (alpha <= 0.0) discard;
        outColor = vec4(fragColor.rgb, fragColor.a * alpha);

    } else if (mode == 2) {
        // ── Stroke SDF quad ───────────────────────────────────────────────
        float dist_to_aaw       = fragUV.x;
        float half_width_to_aaw = fragUV.y;
        float signed_dist       = abs(dist_to_aaw) - half_width_to_aaw;
        float alpha             = smoothstep(0.5, -0.5, signed_dist);
        if (alpha <= 0.0) discard;
        outColor = vec4(fragColor.rgb, fragColor.a * alpha);

    } else if (mode == 3) {
        // ── Analytic SDF fill (rounded rect / circle) ─────────────────────
        // The renderer draws into a 4× SSAA offscreen target that is linearly
        // blitted down to the swapchain.  The blit already contributes ~1
        // swap-pixel of natural geometric AA.  We only need ~1 SSAA pixel of
        // SDF AA for sub-pixel precision — hence the ×2 multiplier.
        // length() (L2) is used instead of fwidth() (L1) so the AA band is
        // uniform across all edge orientations, not 1.4× wider at 45°.
        if (fragColor.a == 0.0) discard;
        float d     = sdRoundedBox(fragUV, vec2(shape.hw, shape.hh), shape.r);
        float aaw   = length(vec2(dFdx(d), dFdy(d))) * 3.0;
        float alpha = smoothstep(aaw, -aaw, d);
        if (alpha <= 0.0) discard;
        outColor = vec4(fragColor.rgb, fragColor.a * alpha);

    } else if (mode == 4) {
        // ── Analytic SDF stroke (rounded rect / circle) ───────────────────
        if (fragColor.a == 0.0) discard;
        float d     = sdRoundedBox(fragUV, vec2(shape.hw, shape.hh), shape.r);
        float aaw   = length(vec2(dFdx(d), dFdy(d))) * 3.0;
        float ring  = abs(d) - shape.sw;
        float alpha = smoothstep(aaw, -aaw, ring);
        if (alpha <= 0.0) discard;
        outColor = vec4(fragColor.rgb, fragColor.a * alpha);

    } else if (mode == 5) {
        // ── Textured quad (Image input) ───────────────────────────────────
        // fragUV = (0,0) top-left … (1,1) bottom-right of the image.
        // fragColor.a carries per-input opacity (set by the Opacity vertex shader).
        vec4 texColor = texture(texSampler, fragUV);
        if (texColor.a == 0.0) discard;
        outColor = vec4(texColor.rgb, texColor.a * fragColor.a);
    }
}
