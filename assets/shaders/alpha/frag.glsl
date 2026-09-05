#version 450

// Scale a finished layer's alpha. Used as a comp's flush pass instead of
// Passthrough: the comp's members are already flattened into one layer here, so
// fading THIS is one flat fade, where fading each member lets them show through
// each other wherever they overlap.
//
// p[0] = the multiplier, 0..1. Straight (non-premultiplied) alpha, matching
// every other layer in this renderer.

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    float p[6];
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    outColor    = texture(tex, fragUV);
    outColor.a *= pc.p[0];
}
