#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;
    float texelY;
    float p[6];     // p[0] = amount in [0, 1], 0 = no change
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4 c     = texture(tex, fragUV);
    vec4 up    = texture(tex, fragUV + vec2(0.0, -pc.texelY));
    vec4 down  = texture(tex, fragUV + vec2(0.0, pc.texelY));
    vec4 left  = texture(tex, fragUV + vec2(-pc.texelX, 0.0));
    vec4 right = texture(tex, fragUV + vec2(pc.texelX, 0.0));

    vec3 sharpened = c.rgb * 5.0 - up.rgb - down.rgb - left.rgb - right.rgb;
    vec3 rgb       = mix(c.rgb, sharpened, clamp(pc.p[0], 0.0, 1.0));

    outColor = vec4(clamp(rgb, 0.0, 1.0), c.a);
}
