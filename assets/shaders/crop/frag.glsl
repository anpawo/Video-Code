#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    float p[6];     // p[0..3] = uMin, vMin, uMax, vMax — absolute UV crop bounds
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4 c = texture(tex, fragUV);
    if (fragUV.x < pc.p[0] || fragUV.x > pc.p[2] || fragUV.y < pc.p[1] || fragUV.y > pc.p[3])
        c.a = 0.0;
    outColor = c;
}
