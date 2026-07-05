#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    float p[6];     // p[0] = levels per channel (>= 2)
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4  c = texture(tex, fragUV);
    float n = max(pc.p[0], 2.0);
    // floor(c*n)/(n-1) spreads the n steps across the full 0..1 range
    // (dividing by n would never reach pure white).
    vec3 q = clamp(floor(c.rgb * n) / (n - 1.0), 0.0, 1.0);
    outColor = vec4(q, c.a);
}
