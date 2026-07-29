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
    // p[0..3] = uMin, vMin, uMax, vMax of the host shape, in absolute frame UV
    // p[4..5] = the origin inside that box — percent of it, or pixels from its
    //           top-left when p[6] is 1. 50/50 (the default) is its centre,
    //           and this shader slides its pattern so the middle lands there.
    // p[6]    = origin unit: 0 = percent, 1 = pixels
    // p[7]    = fps      (set automatically by the Python binding)
    // p[8]    = quality  (0..1 — plasma is cheap enough to ignore it, but the
    //           binding always sends it, so the slot exists in every math shader)
    // p[9]    = scale    (pattern zoom around the origin — <1 shrinks it)
    // p[10]   = speed    (time multiplier)
    // p[11]   = elapsed frames since the effect started (appended per-frame by
    //           MathShader::paramsAtFrame)
    float p[12];
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

    float T = pc.p[11] / max(pc.p[7], 1.0) * pc.p[10];   // elapsed seconds × speed
    // Every math shader draws around its HOST's box, not the frame's: the
    // renderer hands it the box (p[0..3]) and the origin inside it (p[4..6]).
    // Clamped to the frame: the box is absolute frame UV, so a host that
    // spills outside centres the pattern on the part you can actually see —
    // and a renderer that hands over a bogus box (rendering at a size the
    // world transform doesn't follow, say) degrades to the frame instead of
    // throwing the pattern into deep space.
    vec2 boxMin = clamp(vec2(pc.p[0], pc.p[1]), 0.0, 1.0);
    vec2 boxSize = clamp(vec2(pc.p[2], pc.p[3]), 0.0, 1.0) - boxMin;
    vec2 origin = pc.p[6] > 0.5
                      ? boxMin + vec2(pc.p[4], pc.p[5]) * vec2(pc.texelX, pc.texelY)
                      : boxMin + vec2(pc.p[4], pc.p[5]) * 0.01 * boxSize;

    float scale = max(pc.p[9], 0.001);   // pattern zoom, around the origin
    vec2  uv = ((fragUV - origin) / scale + 0.5) * 6.0;

    // Three drifting sine fields interfering.
    float v = sin(uv.x + T)
            + sin((uv.y + T) * 0.7)
            + sin((uv.x + uv.y + T) * 0.5)
            + sin(length(uv - vec2(3.0 + sin(T) * 2.0, 3.0 + cos(T) * 2.0)) * 1.3);

    // Map the interference value to a rolling palette.
    vec3 color = 0.5 + 0.5 * cos(3.14159 * v + vec3(0.0, 2.094, 4.188));

    outColor = vec4(color, coverage);
}
