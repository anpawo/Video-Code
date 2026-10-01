#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    // p[0..3] = object bounding box as absolute UVs (uMin, vMin, uMax, vMax),
    //           prepended by resolveEffectParams() (needsBBox).
    // p[4] = softness, as a fraction (0..0.5) of the box's shorter side.
    float p[8];
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4 c = texture(tex, fragUV);

    vec2 bbMin = vec2(pc.p[0], pc.p[1]);
    vec2 bbMax = vec2(pc.p[2], pc.p[3]);
    vec2 texel = vec2(pc.texelX, pc.texelY);

    vec2 sizePx  = (bbMax - bbMin) / texel;
    vec2 localPx = (fragUV - bbMin) / texel;

    // Distance to the nearest of the four edges, in pixels.
    float distToEdge = min(min(localPx.x, sizePx.x - localPx.x),
                            min(localPx.y, sizePx.y - localPx.y));

    float softnessPx = max(pc.p[4], 0.0) * min(sizePx.x, sizePx.y);
    float edge        = smoothstep(0.0, max(softnessPx, 1e-4), distToEdge);
    outColor          = vec4(c.rgb, c.a * edge);
}
