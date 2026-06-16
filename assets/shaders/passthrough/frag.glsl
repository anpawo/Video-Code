#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    float p[6];
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    outColor = texture(tex, fragUV);
}
