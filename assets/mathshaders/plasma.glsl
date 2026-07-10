#version 450

// Plasma — the second bundled math shader, and the template to copy for your
// own: a classic, CHEAP sine-interference plasma (no raymarch — a handful of
// sin() per pixel, ~100x lighter than silk). Loaded at runtime through
// mathShader("assets/mathshaders/plasma.glsl"); every file used this way must
// follow this exact interface (in/sampler/push-constant/out declarations and
// the p[] layout below).

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;   // 1 / frame width
    float texelY;   // 1 / frame height
    // Args arrive ALPHABETICALLY from the C++ json (see docs/ADDING_EFFECTS.md):
    // p[0] = fps      (set automatically by the Python binding)
    // p[1] = quality  (0..1 — plasma is cheap enough to ignore it, but the
    //        binding always sends it, so the slot exists in every math shader)
    // p[2] = speed    (time multiplier)
    // p[3] = elapsed frames since the effect started (appended per-frame by
    //        MathShader::paramsAtFrame)
    float p[6];
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    // Zero-alpha early-out — see silk.glsl: the effect pass is a fullscreen
    // quad, so skip pixels the host shape doesn't cover.
    float coverage = texture(tex, fragUV).a;
    if (coverage == 0.0) {
        outColor = vec4(0.0);
        return;
    }

    float T = pc.p[3] / max(pc.p[0], 1.0) * pc.p[2];   // elapsed seconds × speed
    vec2  uv = fragUV * 6.0;

    // Three drifting sine fields interfering.
    float v = sin(uv.x + T)
            + sin((uv.y + T) * 0.7)
            + sin((uv.x + uv.y + T) * 0.5)
            + sin(length(uv - vec2(3.0 + sin(T) * 2.0, 3.0 + cos(T) * 2.0)) * 1.3);

    // Map the interference value to a rolling palette.
    vec3 color = 0.5 + 0.5 * cos(3.14159 * v + vec3(0.0, 2.094, 4.188));

    outColor = vec4(color, coverage);
}
