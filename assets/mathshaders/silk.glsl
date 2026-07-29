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
    // Fixed head, then the args ALPHABETICALLY (docs/ADDING_EFFECTS.md):
    // p[0..3] = uMin, vMin, uMax, vMax of the host shape, in absolute frame UV
    // p[4..5] = the origin inside that box — percent of it, or pixels from its
    //           top-left when p[6] is 1. 50/50 (the default) is its centre,
    //           and this shader slides its pattern so the middle lands there.
    // p[6]    = origin unit: 0 = percent, 1 = pixels
    // p[7]    = fps      (set automatically by the Python binding)
    // p[8]    = quality  (0..1, scales the 99 raymarch steps)
    // p[9]    = scale    (pattern zoom around the origin — <1 shrinks it)
    // p[10]   = speed    (time multiplier)
    // p[11]   = elapsed frames since the effect started (appended per-frame by
    //           MathShader::paramsAtFrame)
    float p[12];
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
    vec2  C = ((fragUV - origin) / scale + 0.5) * R;
    float T = pc.p[11] / max(pc.p[7], 1.0) * pc.p[10];   // elapsed seconds × speed
    int   steps = int(99.0 * clamp(pc.p[8], 0.05, 1.0));

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
