#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;   // 1 / frame width
    float texelY;   // 1 / frame height
    // p[0] = intensity (0..1, scales every sub-effect)
    // p[1] = progress  (0..1 over the effect's duration, set per-frame)
    float p[6];
} pc;

layout(location = 0) out vec4 outColor;

float rand(vec2 co) {
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

void main() {
    float k    = pc.p[0];
    float tick = floor(pc.p[1] * 30.0);   // re-roll noise/jitter every frame

    // Analog tracking jitter: whole frame shivers vertically a hair.
    float jitter = (rand(vec2(tick, 3.7)) - 0.5) * 2.0 * pc.texelY * 2.0 * k;
    vec2  uv     = vec2(fragUV.x, fragUV.y + jitter);

    // Chromatic shift: red and blue pull apart horizontally.
    float shift = 1.5 * pc.texelX * k;
    float r = texture(tex, uv + vec2(shift, 0.0)).r;
    vec4  g = texture(tex, uv);
    float b = texture(tex, uv - vec2(shift, 0.0)).b;
    vec3  c = vec3(r, g.g, b);

    // Scanlines: darken every other output row (texelY = one row).
    float row  = floor(fragUV.y / pc.texelY);
    float scan = 1.0 - 0.22 * k * mod(row, 2.0);
    c *= scan;

    // Analog noise.
    float noise = (rand(fragUV + tick * 0.0173) - 0.5) * 0.18 * k;
    c = clamp(c + noise * g.a, 0.0, 1.0);

    outColor = vec4(c, g.a);
}
