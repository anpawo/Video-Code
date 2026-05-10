#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;   // 1/width for H-pass, 0 for V-pass
    float texelY;   // 0 for H-pass, 1/height for V-pass
    float p[6];     // p[0] = sigma (Gaussian standard deviation in pixels)
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    float sigma  = pc.p[0];
    int   radius = min(int(ceil(3.0 * sigma)), 32);
    vec4  sum    = vec4(0.0);
    float total  = 0.0;

    for (int i = -radius; i <= radius; i++) {
        float w      = exp(-float(i * i) / (2.0 * sigma * sigma));
        vec2  offset = vec2(float(i) * pc.texelX, float(i) * pc.texelY);
        sum   += texture(tex, fragUV + offset) * w;
        total += w;
    }

    outColor = sum / total;
}
