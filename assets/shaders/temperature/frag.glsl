#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    float p[6];     // p[0] = warmth, -1 (cool/blue) .. 1 (warm/orange), 0 = unchanged
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4  c = texture(tex, fragUV);
    float k = clamp(pc.p[0], -1.0, 1.0) * 0.2;

    vec3 shifted = c.rgb + vec3(k, 0.0, -k);

    // Push the luma delta back in uniformly so the shift reads as a color
    // temperature change, not a brightness change.
    const vec3 LUMA = vec3(0.2126, 0.7152, 0.0722);
    shifted += dot(c.rgb, LUMA) - dot(shifted, LUMA);

    outColor = vec4(clamp(shifted, 0.0, 1.0), c.a);
}
