#version 450

// "3D Fire" by @XorDev, ported from Shadertoy to the mathShader contract
// (see assets/mathshaders/plasma.glsl for the template, and the technique
// write-up at https://mini.gmshaders.com/p/turbulence).
//
// A raymarched cone of sine-turbulence flames. Roughly HALF silk's cost:
// 50 march steps (vs 99) x ~4 turbulence octaves (the d-loop runs 2 -> 3.3
// -> 5.6 -> 9.3 and exits at 15, vs silk's 6) — measured numbers in the
// fire() binding's docstring.
//
// Port notes vs the original:
// - u_time        -> T (p[3] elapsed frames / p[0] fps * p[2] speed)
// - gl_FragCoord  -> fragUV * R with Y flipped (GL puts y=0 at the BOTTOM,
//                    our fragUV starts at the top — without the flip the
//                    flames point down)
// - fragColor*=i  -> explicit acc = vec4(0) (golfed zero-init)
// - i++ < 50      -> plain counted loop; the original's for-increment
//                    accumulation runs AFTER the body, kept in that order
// - quality       -> scales the 50 march steps, like silk

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
    // p[4]    = quality  (0..1, scales the 50 raymarch steps)
    // p[5]    = scale    (pattern zoom around the origin — <1 shrinks it)
    // p[6]    = speed    (time multiplier)
    // p[7]    = elapsed frames since the effect started (appended per-frame by
    //           MathShader::paramsAtFrame)
    float p[8];
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    // Zero-alpha early-out — the effect pass is a fullscreen quad; skip
    // pixels the host shape doesn't cover.
    float coverage = texture(tex, fragUV).a;
    if (coverage == 0.0) {
        outColor = vec4(0.0);
        return;
    }

    vec2  R = vec2(1.0 / pc.texelX, 1.0 / pc.texelY);
    // Every math shader draws around its HOST, not the frame: the renderer
    // resolved the origin and the unit against whichever box `space` chose,
    // so this file just reads them. Halving is folded into the 2.0 below —
    // one full box height per pattern unit, matching the old frame-sized
    // mapping when the host fills the frame.
    vec2  origin = vec2(pc.p[0], pc.p[1]);
    float unit = max(pc.p[2], 1e-6);

    float scale = max(pc.p[5], 0.001);   // pattern zoom, around the origin
    vec2  S = (fragUV - origin) / (2.0 * unit * scale) + 0.5;
    vec2  I = vec2(S.x, 1.0 - S.y) * R;                // GL-style y-up coords
    float T = pc.p[7] / max(pc.p[3], 1.0) * pc.p[6];   // elapsed seconds × speed
    int   steps = int(50.0 * clamp(pc.p[4], 0.05, 1.0));

    float z = 0.0;                 // raymarched depth
    float d = 0.0;                 // step size / turbulence frequency
    vec4  acc = vec4(0.0);

    vec3 dir = normalize(vec3(I + I, 0.0) - vec3(R.x, R.y, R.y));

    for (int i = 0; i < steps; i++) {
        vec3 p = z * dir;

        // Shift back and animate.
        p.z += 5.0 + cos(T);

        // Twist and rotate, expanding upward. NOTE: the original's `p.xz *= m`
        // is row-vector × matrix in GLSL — keep that order (v*m != m*v here).
        vec4 c = cos(p.y * 0.5 + vec4(0.0, 33.0, 11.0, 0.0));
        p.xz = p.xz * (mat2(c.x, c.y, c.z, c.w) / max(p.y * 0.1 + 1.0, 0.1));

        // Turbulence: waves of increasing frequency (~4 octaves).
        for (d = 2.0; d < 15.0; d /= 0.6) {
            p += cos((p.yzx - vec3(T * 10.0, T, d)) * d) / d;
        }

        // Approximate distance to a hollow cone + march.
        d = 0.01 + abs(length(p.xz) + p.y * 0.3 - 0.5) / 7.0;
        z += d;

        // Fire palette accumulation, brighter near the cone (1/d).
        acc += (sin(z / 3.0 + vec4(7.0, 2.0, 3.0, 0.0)) + 1.1) / d;
    }

    vec3 color = tanh(acc / 1e3).rgb;   // soft tonemap

    outColor = vec4(color, coverage);
}
