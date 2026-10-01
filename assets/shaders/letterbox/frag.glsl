#version 450

layout(location = 0) in vec2 fragUV;

layout(set = 0, binding = 0) uniform sampler2D tex;

layout(push_constant) uniform PC {
    float texelX;   // 1/frameWidth
    float texelY;   // 1/frameHeight
    float p[6];     // p[0] = target aspect ratio (width / height)
} pc;

layout(location = 0) out vec4 outColor;

void main() {
    vec4  c           = texture(tex, fragUV);
    float frameAspect = pc.texelY / max(pc.texelX, 1e-9);   // frame width / height
    float ratio       = max(pc.p[0], 1e-4);

    bool bar = false;
    if (ratio > frameAspect) {
        // Target is wider than the frame: bars top/bottom.
        float barFrac = (1.0 - frameAspect / ratio) * 0.5;
        bar = fragUV.y < barFrac || fragUV.y > 1.0 - barFrac;
    } else if (ratio < frameAspect) {
        // Target is narrower than the frame: bars left/right.
        float barFrac = (1.0 - ratio / frameAspect) * 0.5;
        bar = fragUV.x < barFrac || fragUV.x > 1.0 - barFrac;
    }

    outColor = bar ? vec4(0.0, 0.0, 0.0, 1.0) : c;
}
