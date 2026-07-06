#version 450

// Glow/bloom — the ADDITIVE-COMBINE half only. This fragment shader does NOT
// produce the whole glow: it samples the pre-blurred copy of the input and
// scales it by intensity. The actual "+ sharp original" is done by the
// fixed-function blend stage (ONE, ONE) of the hand-built glow-combine
// pipeline (blendEnable = VK_TRUE, LOAD render pass) — see the `lower == "glow"`
// branch in both renderers. This folder is deliberately EXCLUDED from the
// generic effect-pipeline auto-discovery (which bakes blendEnable = VK_FALSE +
// a CLEAR render pass), so it never becomes a normal single-pass effect.

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex; // the blurred copy of the input

layout(push_constant) uniform PC {
    float texelX;   // unused here (0)
    float texelY;   // unused here (0)
    float p[6];     // p[0] = intensity — scales the additive halo contribution
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    // Straight (non-premultiplied) alpha: scale colour and coverage alike so a
    // faint halo edge (small alpha in the blurred copy) contributes proportionally.
    outColor = texture(tex, fragUV) * pc.p[0];
}
