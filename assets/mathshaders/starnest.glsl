#version 450

// "Star Nest" by Pablo Roman Andrioli (Kali) — ported from Shadertoy to the
// mathShader contract (see assets/mathshaders/plasma.glsl for the template).
// Original: https://www.shadertoy.com/view/XlfGRj — "This content is under
// the MIT License."
//
// A volumetric fractal starfield/nebula — one of the most famous shaders
// ever written, and CHEAP for how it looks: its loops are pure
// abs/dot/length math (no sin/cos inside), unlike the silk/fire raymarchers.
//
// Port notes vs the original:
// - iTime  -> T (p[3] elapsed frames / p[0] fps * p[2] speed); the
//   original's own 0.010 speed factor is kept so speed=1.0 looks canonical
// - iMouse -> fixed at (0,0): a1=0.5, a2=0.8 — the original's no-mouse view
// - quality scales the 20 volumetric steps

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;   // 1 / frame width
    float texelY;   // 1 / frame height
    // p[0] = fps, p[1] = quality, p[2] = speed (alphabetical),
    // p[3] = elapsed frames (appended per-frame by MathShader) — see
    // docs/ADDING_EFFECTS.md.
    float p[6];
} pc;

layout(location = 0) out vec4 outColor;

// Original's tuning constants, unchanged.
const int   ITERATIONS = 17;
const float FORMUPARAM = 0.53;
const float STEPSIZE   = 0.1;
const float ZOOM       = 0.800;
const float TILE       = 0.850;
const float SPEED      = 0.010;
const float BRIGHTNESS = 0.0015;
const float DARKMATTER = 0.300;
const float DISTFADING = 0.730;
const float SATURATION = 0.850;

void main() {
    // Zero-alpha early-out — the effect pass is a fullscreen quad; skip
    // pixels the host shape doesn't cover.
    float coverage = texture(tex, fragUV).a;
    if (coverage == 0.0) {
        outColor = vec4(0.0);
        return;
    }

    vec2  R = vec2(1.0 / pc.texelX, 1.0 / pc.texelY);
    float T = pc.p[3] / max(pc.p[0], 1.0) * pc.p[2];   // elapsed seconds × speed
    int   volsteps = int(20.0 * clamp(pc.p[1], 0.05, 1.0));

    // Aspect-corrected centered coordinates (Y flipped: GL is y-up).
    vec2 uv = vec2(fragUV.x, 1.0 - fragUV.y) - 0.5;
    uv.y *= R.y / R.x;

    vec3  dir = vec3(uv * ZOOM, 1.0);
    float time = T * SPEED + 0.25;

    // Fixed camera rotation (the original's mouse-at-origin view).
    float a1 = 0.5;
    float a2 = 0.8;
    mat2  rot1 = mat2(cos(a1), sin(a1), -sin(a1), cos(a1));
    mat2  rot2 = mat2(cos(a2), sin(a2), -sin(a2), cos(a2));
    dir.xz *= rot1;
    dir.xy *= rot2;

    vec3 from = vec3(1.0, 0.5, 0.5);
    from += vec3(time * 2.0, time, -2.0);
    from.xz *= rot1;
    from.xy *= rot2;

    // Volumetric rendering.
    float s = 0.1;
    float fade = 1.0;
    vec3  v = vec3(0.0);
    for (int r = 0; r < volsteps; r++) {
        vec3 p = from + s * dir * 0.5;
        p = abs(vec3(TILE) - mod(p, vec3(TILE * 2.0)));   // tiling fold

        float pa = 0.0;
        float a = 0.0;
        for (int i = 0; i < ITERATIONS; i++) {
            p = abs(p) / dot(p, p) - FORMUPARAM;   // the magic formula
            a += abs(length(p) - pa);              // absolute sum of average change
            pa = length(p);
        }

        float dm = max(0.0, DARKMATTER - a * a * 0.001);   // dark matter
        a *= a * a;                                        // add contrast
        if (r > 6) fade *= 1.0 - dm;                       // don't render near dark matter

        v += fade;
        v += vec3(s, s * s, s * s * s * s) * a * BRIGHTNESS * fade;   // distance coloring
        fade *= DISTFADING;
        s += STEPSIZE;
    }

    v = mix(vec3(length(v)), v, SATURATION);   // color adjust

    outColor = vec4(v * 0.01, coverage);
}
