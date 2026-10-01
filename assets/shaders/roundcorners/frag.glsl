#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    // p[0..3] = object bounding box as absolute UVs (uMin, vMin, uMax, vMax),
    //           prepended by resolveEffectParams() (needsBBox).
    // p[4] = radius, as a fraction (0..0.5) of the box's shorter side.
    float p[8];
} pc;

layout(location = 0) out vec4 outColor;

// Inigo Quilez's rounded-box SDF, evaluated in pixels so a non-square box
// doesn't turn the corners into ellipses.
float sdRoundBox(vec2 p, vec2 halfSize, float r) {
    vec2 q = abs(p) - halfSize + r;
    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}

void main() {
    vec4 c = texture(tex, fragUV);

    vec2 bbMin = vec2(pc.p[0], pc.p[1]);
    vec2 bbMax = vec2(pc.p[2], pc.p[3]);
    vec2 texel = vec2(pc.texelX, pc.texelY);

    vec2 sizePx   = (bbMax - bbMin) / texel;
    vec2 centerUV = (bbMin + bbMax) * 0.5;
    vec2 localPx  = (fragUV - centerUV) / texel;

    float radiusPx = clamp(pc.p[4], 0.0, 0.5) * min(sizePx.x, sizePx.y);
    float dist     = sdRoundBox(localPx, sizePx * 0.5, radiusPx);

    // One-pixel anti-aliased edge: dist is already in pixel units.
    float edge = 1.0 - smoothstep(-0.5, 0.5, dist);
    outColor   = vec4(c.rgb, c.a * edge);
}
