#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    // Alphabetical attribute order (see duotone.py):
    // p[0]    = contrast (0..1 — how hard pixels commit to one of the inks)
    // p[1..3] = darkB, darkG, darkR   (0..1)
    // p[4..6] = lightB, lightG, lightR (0..1)
    float p[8];
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4  c   = texture(tex, fragUV);
    float lum = dot(c.rgb, vec3(0.299, 0.587, 0.114));

    // A linear two-color mix turns mid-luminance pixels into an ugly mud
    // blend (blue+yellow = olive). Push the luminance through an S-curve so
    // pixels commit to one ink or the other — that's what makes editor
    // duotones look like two inks instead of a gradient.
    float curved = smoothstep(0.25, 0.75, lum);
    lum = mix(lum, curved, pc.p[0]);

    vec3 dark  = vec3(pc.p[3], pc.p[2], pc.p[1]);
    vec3 light = vec3(pc.p[6], pc.p[5], pc.p[4]);
    outColor = vec4(mix(dark, light, lum), c.a);
}
