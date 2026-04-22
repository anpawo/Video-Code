#version 450

layout(location = 0) in vec2 fragUV;
layout(location = 1) in vec4 fragColor;
layout(location = 2) in vec4 fragExtra;

layout(set = 0, binding = 0) uniform UBO {
    float time;
    float pad0; float pad1; float pad2;
    float resX;
    float resY;
    float pixelSize;
    float pad3;
} ubo;

layout(set = 1, binding = 0) uniform sampler2D texSampler;

layout(location = 0) out vec4 outColor;

void main() {
    if (fragExtra.x == 5.0) {
        outColor = texture(texSampler, fragUV);
        outColor.a *= fragColor.a;
    } else if (fragExtra.x == 2.0) {
        outColor = fragColor;
    } else {
        outColor = fragColor;
    }
}
