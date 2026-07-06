#version 450

// Track matte / mask — the SECOND hand-built exception to the effect-chain
// rule "an effect samples one texture and never composites" (glow is the
// first). Unlike every generic effect, this pass samples TWO textures, both
// full-frame screen-space renders in the same coordinate system:
//   contentTex = the matte consumer's own isolated layer (input A)
//   matteTex   = the matte source's finished result       (input B)
// A is kept only where B has coverage: out.rgb = A.rgb, out.a = A.a * B.a.
// This folder is deliberately EXCLUDED from the generic single-sampler
// auto-discovery loop (which builds a 1-sampler layout); the 2-sampler
// pipeline + descriptor set are hand-built by createMatteResources().

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D contentTex; // input A (masked)
layout(set = 0, binding = 1) uniform sampler2D matteTex;   // input B (mask)

layout(location = 0) out vec4 outColor;

void main() {
    vec4 c = texture(contentTex, fragUV);
    vec4 m = texture(matteTex, fragUV);
    // Multiply A's coverage by B's alpha: A survives only inside B's silhouette.
    outColor = vec4(c.rgb, c.a * m.a);
}
