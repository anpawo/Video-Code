#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;   // 1/frameWidth — real texel size, single-pass effect
    float texelY;   // 1/frameHeight
    float p[6];     // p[0] = amount, fraction of frame width (typical 0.005)
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec2  dir = fragUV - vec2(0.5);
    float len = length(dir);
    vec2  dirN = len > 1e-6 ? dir / len : vec2(0.0);

    // Same physical pixel-shift magnitude along x and y despite the frame's
    // non-square UV scale (texelX != texelY off a square frame).
    vec2 offset = dirN * pc.p[0] * vec2(1.0, pc.texelY / max(pc.texelX, 1e-9));

    float r = texture(tex, fragUV + offset).r;  // outward
    vec4  g = texture(tex, fragUV);
    float b = texture(tex, fragUV - offset).b;  // inward

    outColor = vec4(r, g.g, b, g.a);
}
