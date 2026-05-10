#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    float p[6];     // p[0] = gamma (1.0 = no change, <1 = brighter, >1 = darker)
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4  c     = texture(tex, fragUV);
    float gamma = max(pc.p[0], 0.001);
    outColor    = vec4(pow(c.rgb, vec3(gamma)), c.a);
}
