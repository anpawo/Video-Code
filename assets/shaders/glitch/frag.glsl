#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    // p[0] = amount (percent of screen width — peak horizontal displacement)
    // p[1] = seed (differentiates simultaneous glitch instances)
    // p[2] = slices (number of horizontal bands)
    // p[3] = progress (0..1 over the effect's duration, set per-frame)
    float p[6];
} pc;

layout(location = 0) out vec4 outColor;

float rand(vec2 co) {
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

void main() {
    float amount = pc.p[0] / 100.0;
    float seed   = pc.p[1];
    float slices = max(pc.p[2], 1.0);

    // Re-roll the slice offsets ~24 times over the effect so the bands jump.
    float tick     = floor(pc.p[3] * 24.0);
    float sliceIdx = floor(fragUV.y * slices);

    float r1 = rand(vec2(sliceIdx, seed + tick * 0.371));
    float r2 = rand(vec2(sliceIdx + 31.7, seed + tick * 0.173));

    // Only ~40% of the slices shift on any given tick.
    float off = (r1 * 2.0 - 1.0) * amount * step(0.6, r2);

    vec2  uv     = vec2(fragUV.x + off, fragUV.y);
    float rgbOff = amount * 0.35;

    vec4 cr = texture(tex, uv + vec2(rgbOff, 0.0));
    vec4 cg = texture(tex, uv);
    vec4 cb = texture(tex, uv - vec2(rgbOff, 0.0));

    // Take the widest alpha so the split channels stay visible at the edges.
    float a = max(cg.a, max(cr.a, cb.a));
    outColor = vec4(cr.r, cg.g, cb.b, a);
}
