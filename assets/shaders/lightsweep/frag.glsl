#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    // p[0..3] = object bounding box as absolute UVs (uMin, vMin, uMax, vMax),
    //           resolved per-mesh in setMeshes() like the Crop shader.
    // p[4] = angle (degrees, 0 = vertical band sweeping left -> right)
    // p[5] = intensity (0..1 additive white highlight)
    // p[6] = band width (percent of the bounding box, 0-100)
    // p[7] = progress (0..1 over the effect's duration, set per-frame)
    float p[8];
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4 c = texture(tex, fragUV);

    vec2 bbMin = vec2(pc.p[0], pc.p[1]);
    vec2 bbMax = vec2(pc.p[2], pc.p[3]);
    vec2 local = (fragUV - bbMin) / max(bbMax - bbMin, vec2(1e-6));

    // Project onto the sweep direction, normalized so t spans 0..1 across the
    // bounding box whatever the angle.
    float angle = radians(pc.p[4]);
    vec2  dir   = vec2(cos(angle), sin(angle));
    float pMin  = min(0.0, dir.x) + min(0.0, dir.y);
    float pMax  = max(0.0, dir.x) + max(0.0, dir.y);
    float t     = (dot(local, dir) - pMin) / max(pMax - pMin, 1e-6);

    // Band center travels from -width to 1+width so it fully enters and exits.
    float width  = max(pc.p[6] / 100.0, 1e-6);
    float center = mix(-width, 1.0 + width, pc.p[7]);
    float band   = clamp(1.0 - abs(t - center) / width, 0.0, 1.0);
    band         = band * band * (3.0 - 2.0 * band); // smoothstep falloff

    // Additive white highlight, masked by the object's alpha.
    outColor = vec4(c.rgb + band * pc.p[5] * c.a, c.a);
}
