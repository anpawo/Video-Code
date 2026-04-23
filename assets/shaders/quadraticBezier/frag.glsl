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
    int mode = int(fragExtra.x);

    if (mode == 3) {
        // Textured quad — uv = texture coordinates, color.a = opacity multiplier
        outColor    = texture(texSampler, fragUV);
        outColor.a *= fragColor.a;

    } else if (mode == 2) {
        // Polyline stroke — uv.x = signed dist from centreline, uv.y = half-width
        float dist = abs(fragUV.x);
        float edge = fragUV.y;
        float aaw  = max(fwidth(dist), 0.0001);
        float a    = 1.0 - smoothstep(edge - aaw, edge + aaw, dist);
        outColor   = fragColor;
        outColor.a *= a;

    } else if (mode == 1) {
        // Bezier cap — Loop-Blinn: k = u² - v; k > 0 is outside the curve
        float k   = fragUV.x * fragUV.x - fragUV.y;
        float aaw = max(fwidth(k), 0.0001);
        float a   = 1.0 - smoothstep(-aaw, aaw, k);
        outColor  = fragColor;
        outColor.a *= a;

    } else {
        // mode == 0: solid fill triangle
        outColor = fragColor;
    }
}
