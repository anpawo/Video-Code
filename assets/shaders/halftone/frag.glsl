#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;   // 1 / frame width
    float texelY;   // 1 / frame height
    float p[6];     // p[0] = dot-grid cell size in screen pixels
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    float cell = max(pc.p[0], 2.0);

    // Work in screen-pixel coordinates, on a 45°-rotated grid (the classic
    // print-screen angle — axis-aligned grids look digital, not printed).
    vec2  px  = fragUV / vec2(pc.texelX, pc.texelY);
    float s   = 0.70710678; // sin/cos 45°
    vec2  rot = vec2(px.x * s - px.y * s, px.x * s + px.y * s);

    vec2 cellIdx    = floor(rot / cell);
    vec2 cellCenter = (cellIdx + 0.5) * cell;

    // Sample the source at the CELL CENTER (unrotate back to UV) so each
    // dot has one uniform color/brightness.
    vec2 back = vec2(cellCenter.x * s + cellCenter.y * s, -cellCenter.x * s + cellCenter.y * s);
    vec4 src  = texture(tex, back * vec2(pc.texelX, pc.texelY));

    // Dot radius follows darkness: dark cells -> big dots, highlights ->
    // pinpricks. sqrt keeps perceived coverage proportional to tone.
    float lum = dot(src.rgb, vec3(0.299, 0.587, 0.114));
    float r   = sqrt(clamp(1.0 - lum, 0.0, 1.0)) * 0.5 * cell;

    float d   = distance(rot, cellCenter);
    float cov = smoothstep(r + 0.8, r - 0.8, d); // ~1px anti-aliased edge

    outColor = vec4(src.rgb, src.a * cov);
}
