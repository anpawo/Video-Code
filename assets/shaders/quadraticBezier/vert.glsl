#version 450

// Inputs — matches Vertex layout: pos[2], uv[2], color[4], extra[4]
layout(location = 0) in vec2 inPos;
layout(location = 1) in vec2 inUV;
layout(location = 2) in vec4 inColor;
layout(location = 3) in vec4 inExtra; // [0] = draw mode (0=fill, 1=bezier cap, 2=stroke)

layout(location = 0) out vec2 fragUV;
layout(location = 1) out vec4 fragColor;
layout(location = 2) out vec4 fragExtra;

void main() {
    gl_Position = vec4(inPos, 0.0, 1.0);
    fragUV    = inUV;
    fragColor = inColor;
    fragExtra = inExtra;
}
