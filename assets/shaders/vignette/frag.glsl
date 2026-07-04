#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    // p[0..3] = object bounding box as absolute UVs (uMin, vMin, uMax, vMax),
    //           resolved per-mesh in setMeshes() like the Crop shader.
    // p[4] = intensity (0..1 — maximum darkening at the corners)
    // p[5] = radius (percent of the half-diagonal where darkening begins)
    // p[6] = smoothness (percent falloff width past the radius)
    float p[8];
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4 c = texture(tex, fragUV);

    vec2 bbMin = vec2(pc.p[0], pc.p[1]);
    vec2 bbMax = vec2(pc.p[2], pc.p[3]);
    vec2 local = (fragUV - bbMin) / max(bbMax - bbMin, vec2(1e-6));

    // Distance from the bbox center, normalized so the corners sit at 1.
    float d = distance(local, vec2(0.5)) * 2.0 / sqrt(2.0);

    float radius     = pc.p[5] / 100.0;
    float smoothness = max(pc.p[6] / 100.0, 1e-4);
    float vig        = smoothstep(radius, radius + smoothness, d) * pc.p[4];

    outColor = vec4(c.rgb * (1.0 - vig), c.a);
}
