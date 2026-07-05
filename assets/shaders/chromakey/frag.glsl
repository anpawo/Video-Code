#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    // Alphabetical attribute order (see chromaKey.py) — keyB/keyG/keyR sort
    // before softness/tolerance:
    // p[0..2] = keyB, keyG, keyR (0..1)
    // p[3]    = softness  (0..1)
    // p[4]    = tolerance (0..1)
    float p[6];
} pc;

layout(location = 0) out vec4 outColor;

// Hue/saturation distance (not raw RGB distance) so the key tolerates
// brightness variation across the green screen (lighting gradients,
// shadows) without also tolerating unrelated colors.
vec2 hueSat(vec3 c) {
    float maxc = max(c.r, max(c.g, c.b));
    float minc = min(c.r, min(c.g, c.b));
    float delta = maxc - minc;
    float sat = maxc <= 0.0001 ? 0.0 : delta / maxc;
    if (delta <= 0.0001) return vec2(0.0, sat);
    float hue;
    if (maxc == c.r) hue = mod((c.g - c.b) / delta, 6.0);
    else if (maxc == c.g) hue = (c.b - c.r) / delta + 2.0;
    else hue = (c.r - c.g) / delta + 4.0;
    return vec2(hue / 6.0, sat);
}

void main() {
    vec4 c = texture(tex, fragUV);

    vec3 key = vec3(pc.p[2], pc.p[1], pc.p[0]);
    vec2 hsC = hueSat(c.rgb);
    vec2 hsK = hueSat(key);

    float hueDist = min(abs(hsC.x - hsK.x), 1.0 - abs(hsC.x - hsK.x));
    float dist = length(vec2(hueDist, hsC.y - hsK.y));

    float soft = max(pc.p[3], 0.001);
    float tol  = max(pc.p[4], 0.001);
    float keyAlpha = smoothstep(tol, tol + soft, dist);

    outColor = vec4(c.rgb, c.a * keyAlpha);
}
