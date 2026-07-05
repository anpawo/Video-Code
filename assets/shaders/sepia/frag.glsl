#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    float p[6];     // p[0] = amount (0..1 blend toward full sepia)
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4 c = texture(tex, fragUV);
    vec3 s = vec3(
        dot(c.rgb, vec3(0.393, 0.769, 0.189)),
        dot(c.rgb, vec3(0.349, 0.686, 0.168)),
        dot(c.rgb, vec3(0.272, 0.534, 0.131)));
    outColor = vec4(mix(c.rgb, clamp(s, 0.0, 1.0), pc.p[0]), c.a);
}
