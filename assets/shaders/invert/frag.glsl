#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    float p[6];     // p[0] = amount (0..1 blend toward the full negative)
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4 c = texture(tex, fragUV);
    outColor = vec4(mix(c.rgb, 1.0 - c.rgb, pc.p[0]), c.a);
}
