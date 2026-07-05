#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    float p[6];     // p[0] = hue rotation in degrees
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4  c  = texture(tex, fragUV);
    float a  = radians(pc.p[0]);
    float cs = cos(a);
    float sn = sin(a);

    // CSS filter hue-rotate matrix (luminance-preserving rotation around
    // the gray axis) — rows are the output R/G/B weights.
    mat3 m = mat3(
        0.213 + cs * 0.787 - sn * 0.213, 0.715 - cs * 0.715 - sn * 0.715, 0.072 - cs * 0.072 + sn * 0.928,
        0.213 - cs * 0.213 + sn * 0.143, 0.715 + cs * 0.285 + sn * 0.140, 0.072 - cs * 0.072 - sn * 0.283,
        0.213 - cs * 0.213 - sn * 0.787, 0.715 - cs * 0.715 + sn * 0.715, 0.072 + cs * 0.928 + sn * 0.072);

    // GLSL mat3 columns vs rows: multiply on the left so each row above
    // dots against the color (row-major spec, column-major storage).
    vec3 r = clamp(c.rgb * m, 0.0, 1.0);
    outColor = vec4(r, c.a);
}
