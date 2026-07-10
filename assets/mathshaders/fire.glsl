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
    // p[0] = fps, p[1] = quality, p[2] = speed (alphabetical),
    // p[3] = elapsed frames (appended per-frame by MathShader) — see
    // docs/ADDING_EFFECTS.md.
    float p[6];
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
    vec2  I = vec2(fragUV.x, 1.0 - fragUV.y) * R;      // GL-style y-up coords
    float T = pc.p[3] / max(pc.p[0], 1.0) * pc.p[2];   // elapsed seconds × speed
    int   steps = int(50.0 * clamp(pc.p[1], 0.05, 1.0));

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
