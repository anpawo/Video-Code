#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    float p[6];     // p[0] = strength, p[1] = time/seed
} pc;

layout(location = 0) out vec4 outColor;

float rand(vec2 co) {
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

void main() {
    vec4  c        = texture(tex, fragUV);
    float noise    = rand(fragUV + pc.p[1]) * 2.0 - 1.0;
    float strength = pc.p[0];
    outColor       = vec4(clamp(c.rgb + noise * strength, 0.0, 1.0), c.a);
}
