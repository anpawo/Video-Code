#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    float p[6];     // p[0] = strength (0 = no effect, 1 = full grayscale)
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4  c        = texture(tex, fragUV);
    float gray     = dot(c.rgb, vec3(0.299, 0.587, 0.114));
    float strength = pc.p[0];
    outColor       = vec4(mix(c.rgb, vec3(gray), strength), c.a);
}
