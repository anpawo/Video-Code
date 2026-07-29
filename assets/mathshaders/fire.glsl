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
    // p[0..3] = uMin, vMin, uMax, vMax of the host shape, in absolute frame UV
    // p[4..5] = the origin inside that box — percent of it, or pixels from its
    //           top-left when p[6] is 1. 50/50 (the default) is its centre,
    //           and this shader slides its pattern so the middle lands there.
    // p[6]    = origin unit: 0 = percent, 1 = pixels
    // p[7]    = fps      (set automatically by the Python binding)
    // p[8]    = quality  (0..1, scales the 50 raymarch steps)
    // p[9]    = scale    (pattern zoom around the origin — <1 shrinks it)
    // p[10]   = speed    (time multiplier)
    // p[11]   = elapsed frames since the effect started (appended per-frame by
    //           MathShader::paramsAtFrame)
    float p[12];
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
    vec2  S = (fragUV - origin) / scale + 0.5;
    vec2  I = vec2(S.x, 1.0 - S.y) * R;                // GL-style y-up coords
    float T = pc.p[11] / max(pc.p[7], 1.0) * pc.p[10];   // elapsed seconds × speed
    int   steps = int(50.0 * clamp(pc.p[8], 0.05, 1.0));

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
