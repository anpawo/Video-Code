#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;   // 1 / frame width  — real texel size (non-blur passes)
    float texelY;   // 1 / frame height
    float p[6];     // p[0] = cell size in screen pixels
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec2 cell = vec2(pc.texelX, pc.texelY) * max(pc.p[0], 1.0);
    vec2 uv   = (floor(fragUV / cell) + 0.5) * cell;
    outColor  = texture(tex, uv);
}
