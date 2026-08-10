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
    // Fixed head, then the args ALPHABETICALLY (docs/ADDING_EFFECTS.md):
    // p[0..1] = the pattern's origin, in absolute frame UV — already resolved
    //           by resolveEffectParams from the box `space` selects (the
    //           host's own box by default). The GLSL never sees the box, the
    //           percent/pixel choice, or the mode.
    // p[2]    = the unit: HALF THE BOX'S HEIGHT, in frame UV. Dividing by it
    //           is what makes the pattern scale WITH the host instead of
    //           being resampled as it grows — origin and unit come from the
    //           same box, and that is the whole anti-swim contract.
    // p[3]    = fps      (set automatically by the Python binding)
    // p[4]    = quality  (0..1 — plasma is cheap enough to ignore it, but
    //           the binding always sends it, so every math shader has the slot)
    // p[5]    = scale    (pattern zoom around the origin — <1 shrinks it)
    // p[6]    = speed    (time multiplier)
    // p[7]    = elapsed frames since the effect started (appended per-frame by
    //           MathShader::paramsAtFrame)
    float p[8];
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

    float T = pc.p[7] / max(pc.p[3], 1.0) * pc.p[6];   // elapsed seconds × speed
    // Every math shader draws around its HOST, not the frame: the renderer
    // resolved the origin and the unit against whichever box `space` chose,
    // so this file just reads them. Halving is folded into the 2.0 below —
    // one full box height per pattern unit, matching the old frame-sized
    // mapping when the host fills the frame.
    vec2  origin = vec2(pc.p[0], pc.p[1]);
    float unit = max(pc.p[2], 1e-6);

    float scale = max(pc.p[5], 0.001);   // pattern zoom, around the origin
    vec2  uv = ((fragUV - origin) / (2.0 * unit * scale) + 0.5) * 6.0;

    // Three drifting sine fields interfering.
    float v = sin(uv.x + T)
            + sin((uv.y + T) * 0.7)
            + sin((uv.x + uv.y + T) * 0.5)
            + sin(length(uv - vec2(3.0 + sin(T) * 2.0, 3.0 + cos(T) * 2.0)) * 1.3);

    // Map the interference value to a rolling palette.
    vec3 color = 0.5 + 0.5 * cos(3.14159 * v + vec3(0.0, 2.094, 4.188));

    outColor = vec4(color, coverage);
}
