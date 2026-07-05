#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    // p[0..3] = object bounding box as absolute UVs (uMin, vMin, uMax, vMax),
    //           prepended by resolveEffectParams() (needsBBox).
    // p[4]    = strength (0..1 — fraction of the center->pixel ray sampled)
    float p[6];
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec2 center = vec2((pc.p[0] + pc.p[2]) * 0.5, (pc.p[1] + pc.p[3]) * 0.5);
    vec2 dir    = (fragUV - center) * pc.p[4];

    // 20 taps back along the center->pixel ray, weighted so the sample at
    // the original position dominates: keeps a sharp core with a decaying
    // trail (equal weights read as N discrete ghost copies, not a streak).
    const int N = 20;
    vec4  acc = vec4(0.0);
    float wsum = 0.0;
    for (int i = 0; i < N; ++i) {
        float t = float(i) / float(N - 1);
        float w = 1.0 - 0.85 * t;
        acc += texture(tex, fragUV - dir * t) * w;
        wsum += w;
    }
    outColor = acc / wsum;
}
