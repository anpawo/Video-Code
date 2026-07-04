#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    // p[0..3] = object bounding box as absolute UVs (uMin, vMin, uMax, vMax),
    //           prepended by resolveEffectParams() (needsBBox).
    // p[4..7] = bottom, left, right, top — percent (0-100) of the bounding
    //           box cut away from each side (alphabetical arg order).
    float p[8];
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4 c = texture(tex, fragUV);

    vec2  bbMin = vec2(pc.p[0], pc.p[1]);
    vec2  bbMax = vec2(pc.p[2], pc.p[3]);
    vec2  sz    = bbMax - bbMin;

    // v grows downward in UV space, so "top" trims from vMin.
    float uLo = bbMin.x + pc.p[5] / 100.0 * sz.x;   // left
    float uHi = bbMax.x - pc.p[6] / 100.0 * sz.x;   // right
    float vLo = bbMin.y + pc.p[7] / 100.0 * sz.y;   // top
    float vHi = bbMax.y - pc.p[4] / 100.0 * sz.y;   // bottom

    if (fragUV.x < uLo || fragUV.x > uHi || fragUV.y < vLo || fragUV.y > vHi)
        c.a = 0.0;
    outColor = c;
}
