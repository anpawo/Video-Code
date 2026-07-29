#version 450

// Evil Eye — port of the React Bits <EvilEye /> WebGL component
// (https://reactbits.dev, ogl + a JS-generated noise texture) to the
// mathShader contract. Loaded through evilEye() / mathShader().
//
// Two things had to change to fit the contract, both documented where they
// happen below:
//   1. no second sampler — binding 0 is the host layer, so the component's
//      256x256 CPU-generated fbm texture is regenerated procedurally here
//      (same recipe: 8 octaves, amp *= 0.65, contrast (v-0.5)*2.2+0.5).
//   2. no mouse — the pupil is fixed dead centre, looking straight at you.

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;   // 1 / frame width
    float texelY;   // 1 / frame height
    // Fixed head, then the args ALPHABETICALLY (docs/ADDING_EFFECTS.md):
    // p[0..3] = uMin, vMin, uMax, vMax of the host shape, in absolute frame UV
    // p[4..5] = the origin inside that box — percent of it, or pixels from its
    //           top-left when p[6] is 1. 50/50 (the default) is its centre,
    //           and THE EYE LOOKS AT YOU FROM THERE, wherever the shape sits.
    // p[6]    = origin unit: 0 = percent, 1 = pixels
    // p[7]    = color    (0xRRGGBB packed into one float, exact below 2^24)
    // p[8]    = fps      (set automatically by the Python binding)
    // p[9]    = intensity
    // p[10]   = pupilSize
    // p[11]   = quality  (0..1 — octave count of the procedural noise)
    // p[12]   = scale
    // p[13]   = speed
    // p[14]   = elapsed frames since the effect started
    float p[15];
} pc;

layout(location = 0) out vec4 outColor;

// Baked: the component exposes these, the push constant has no room left.
const float IRIS_WIDTH = 0.25;
const float GLOW_INTENSITY = 0.35;
const float NOISE_SCALE = 1.0;

// --- procedural stand-in for the component's noise texture -----------------
// The JS builds a 256x256 RGBA texture on the CPU and samples it with REPEAT
// wrapping. We have no second sampler, so the same field is evaluated
// directly: a value-noise lattice that wraps every `freq` cells (mod, like the
// JS modulo) and bilinear interpolation (linear, not smoothstep — the JS
// interpolates linearly and the creased look comes from that).

float hash(vec2 cell, float seed)
{
    return fract(sin(dot(cell, vec2(127.1, 311.7)) + seed * 74.7) * 43758.5453123);
}

float vnoise(vec2 uv, float freq, float seed)
{
    vec2  f = uv * freq;
    vec2  i = floor(f);
    vec2  t = f - i;
    vec2  i0 = mod(i, freq);
    vec2  i1 = mod(i + 1.0, freq);
    float v00 = hash(vec2(i0.x, i0.y), seed);
    float v10 = hash(vec2(i1.x, i0.y), seed);
    float v01 = hash(vec2(i0.x, i1.y), seed);
    float v11 = hash(vec2(i1.x, i1.y), seed);
    return mix(mix(v00, v10, t.x), mix(v01, v11, t.x), t.y);
}

float fbm(vec2 uv, int octaves)
{
    float v = 0.0;
    float amp = 0.4;
    float total = 0.0;
    for (int o = 0; o < octaves; o++) {
        v += amp * vnoise(uv, 32.0 * exp2(float(o)), float(o) * 31.0);
        total += amp;
        amp *= 0.65;
    }
    v /= total;
    return clamp((v - 0.5) * 2.2 + 0.5, 0.0, 1.0);   // the JS contrast curve
}

void main()
{
    // Zero-alpha early-out — the effect pass is a fullscreen quad, so skip
    // pixels the host shape doesn't cover.
    float coverage = texture(tex, fragUV).a;
    if (coverage == 0.0) {
        outColor = vec4(0.0);
        return;
    }

    float packed = pc.p[7];
    vec3  eyeColor = vec3(floor(packed / 65536.0), floor(mod(packed, 65536.0) / 256.0), mod(packed, 256.0)) / 255.0;
    float intensity = pc.p[9];
    float pupilSize = pc.p[10];
    int   octaves = int(clamp(pc.p[11], 0.0, 1.0) * 4.0) + 4;
    float scale = max(pc.p[12], 0.001);

    // The component works in (fragCoord*2 - res)/res.y: centred, y up, x in
    // [-aspect, aspect]. Same frame here, but built around the HOST's box
    // instead of the frame's, so the eye sits in the middle of its shape:
    // the box's own half-height is the unit, which also makes the eye scale
    // with the shape instead of with the render resolution.
    // Clamped to the frame — see the note in silk.glsl.
    vec2  boxMin = clamp(vec2(pc.p[0], pc.p[1]), 0.0, 1.0);
    vec2  boxSize = clamp(vec2(pc.p[2], pc.p[3]), 0.0, 1.0) - boxMin;
    vec2  origin = pc.p[6] > 0.5
                       ? boxMin + vec2(pc.p[4], pc.p[5]) * vec2(pc.texelX, pc.texelY)
                       : boxMin + vec2(pc.p[4], pc.p[5]) * 0.01 * boxSize;
    float halfH = max(boxSize.y * 0.5, 1e-6);
    float aspect = pc.texelY / pc.texelX;   // frame width / height
    vec2  uv = vec2((fragUV.x - origin.x) * aspect, origin.y - fragUV.y) / (halfH * scale);

    float ft = pc.p[14] / max(pc.p[8], 1.0) * pc.p[13];   // elapsed seconds × speed

    float polarRadius = length(uv) * 2.0;
    float polarAngle = (2.0 * atan(uv.x, uv.y)) / 6.28 * 0.3;
    vec2  polarUv = vec2(polarRadius, polarAngle);

    float noiseA = fbm(polarUv * vec2(0.2, 7.0) * NOISE_SCALE + vec2(-ft * 0.1, 0.0), octaves);
    float noiseB = fbm(polarUv * vec2(0.3, 4.0) * NOISE_SCALE + vec2(-ft * 0.2, 0.0), octaves);
    float noiseC = fbm(polarUv * vec2(0.1, 5.0) * NOISE_SCALE + vec2(-ft * 0.1, 0.0), octaves);

    float distanceMask = 1.0 - length(uv);

    // Inner ring
    float innerRing = clamp(-1.0 * ((distanceMask - 0.7) / IRIS_WIDTH), 0.0, 1.0);
    innerRing = (innerRing * distanceMask - 0.2) / 0.28;
    innerRing += noiseA - 0.5;
    innerRing *= 1.3;
    innerRing = clamp(innerRing, 0.0, 1.0);

    float outerRing = clamp(-1.0 * ((distanceMask - 0.5) / 0.2), 0.0, 1.0);
    outerRing = (outerRing * distanceMask - 0.1) / 0.38;
    outerRing += noiseC - 0.5;
    outerRing *= 1.3;
    outerRing = clamp(outerRing, 0.0, 1.0);

    innerRing += outerRing;

    // Inner eye
    float innerEye = distanceMask - 0.1 * 2.0;
    innerEye *= noiseB * 2.0;

    // Pupil — dead centre: the component offsets it by the cursor, we have no
    // cursor and the eye is meant to stare straight ahead.
    float pupil = 1.0 - length(uv * vec2(9.0, 2.3));
    pupil *= pupilSize;
    pupil = clamp(pupil, 0.0, 1.0);
    pupil /= 0.35;

    // Outer eye
    float outerEyeGlow = 1.0 - length(uv * vec2(0.5, 1.5));
    outerEyeGlow = clamp(outerEyeGlow + 0.5, 0.0, 1.0);
    outerEyeGlow += noiseC - 0.5;
    float outerBgGlow = outerEyeGlow;
    outerEyeGlow = pow(outerEyeGlow, 2.0);
    outerEyeGlow += distanceMask;
    outerEyeGlow *= GLOW_INTENSITY;
    outerEyeGlow = clamp(outerEyeGlow, 0.0, 1.0);
    outerEyeGlow *= pow(1.0 - distanceMask, 2.0) * 2.5;

    // Outer eye bg glow
    outerBgGlow += distanceMask;
    outerBgGlow = pow(max(outerBgGlow, 0.0), 0.5);
    outerBgGlow *= 0.15;

    vec3 color = eyeColor * intensity * clamp(max(innerRing + innerEye, outerEyeGlow + outerBgGlow) - pupil, 0.0, 3.0);

    outColor = vec4(color, coverage);
}
