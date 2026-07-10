#version 450

// Silk — procedural "math shader": raymarched sine-turbulence silk, ported
// from the golfed fragcoord.xyz dialect (original: fragcoord.xyz/s/ae4trrxh).
// Unlike every other effect here, this one REPLACES the input's RGB with a
// generated pattern instead of filtering it — only the input's own alpha is
// kept, so the pattern stays inside the host shape's coverage (and its
// antialiased edges), and composes with .matte() like any other content.
//
// DSL → GLSL notes (fragcoord golf conventions):
//   f/f3/f4 = float/vec3/vec4 (zero-init) · @(n) = repeat n times
//   R = resolution · C = fragCoord · T = seconds · O = output (accumulator)
//   f4(,1,2,)  = vec4(0,1,2,0) · `.06*i++` = phase from the outer loop index
//   `z += d = …` assigns the step then advances the ray.
// C.z (fragCoord depth, ~0..1) is negligible against R.y in the ray
// direction, so it is dropped here.

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;   // 1 / frame width
    float texelY;   // 1 / frame height
    // Args arrive ALPHABETICALLY from the C++ json (see docs/ADDING_EFFECTS.md):
    // p[0] = fps      (set automatically by the Python binding)
    // p[1] = quality  (0..1, scales the march step count — 1.0 = the
    //        original's 99 steps; lower is cheaper and dimmer/softer)
    // p[2] = speed    (time multiplier, 1.0 = the original's clock)
    // p[3] = elapsed frames since the effect started (appended per-frame by
    //        Silk::paramsAtFrame — raw frames, not 0..1 progress: a
    //        procedural animation needs an unbounded clock)
    float p[6];
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    // The effect pass draws a FULLSCREEN quad, so most pixels can be outside
    // the host shape entirely. Their output alpha would be 0 anyway — skip
    // the whole march for them. This is the difference between "costs the
    // full frame" and "costs the shape's coverage" (~2-3× for typical hosts).
    float coverage = texture(tex, fragUV).a;
    if (coverage == 0.0) {
        outColor = vec4(0.0);
        return;
    }

    vec2  R = vec2(1.0 / pc.texelX, 1.0 / pc.texelY);
    vec2  C = fragUV * R;
    float T = pc.p[3] / max(pc.p[0], 1.0) * pc.p[2];   // elapsed seconds × speed
    int   steps = int(99.0 * clamp(pc.p[1], 0.05, 1.0));

    // Ray from the camera through this pixel: nor(R.xyy - 2*C.rgb).
    vec3 dir = normalize(vec3(R.x - 2.0 * C.x, R.y - 2.0 * C.y, R.y));

    float z = 0.0;                 // distance marched along the ray
    float d = 0.0;                 // current step estimate
    vec4  acc = vec4(0.0);         // color accumulator (O)

    for (int i = 0; i < steps; i++) {
        vec3 p = z * dir;

        // Sine turbulence: 6 octaves of axis-swizzled displacement.
        d = 2.0;
        for (int j = 0; j < 6; j++) {
            d /= 0.9;
            p = p.zxy + sin(p * d + d + T * 0.5) / d;
        }

        // Distance estimate + march: thin bright sheets around p.z ≈ 2.
        d = 0.001 + abs(2.0 - mix(z, p.z, 0.4)) / 9.0;
        z += d;

        // Phase-shifted rainbow accumulation, brighter near the sheets (1/d).
        acc += (sin(z + 0.06 * float(i) + vec4(0.0, 1.0, 2.0, 0.0)) + 1.0) / d;
    }

    vec3 color = tanh(acc / 3e4).rgb;   // soft tonemap, O = tanh(O/3e4)

    // Content replacement: generated RGB, host coverage as alpha.
    outColor = vec4(color, coverage);
}
