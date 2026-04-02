#pragma once
#include <vulkan/vulkan.h>

#include <string>
#include <vector>

// compileGLSL
//   Compiles a GLSL source string to a SPIR-V binary at runtime using
//   the glslang library (the reference Khronos compiler).
//
//   Parameters:
//     source  — full GLSL source text (e.g. the content of a .vert / .frag)
//     stage   — which shader stage this source belongs to
//               (VK_SHADER_STAGE_VERTEX_BIT or VK_SHADER_STAGE_FRAGMENT_BIT)
//
//   Returns a vector of 32-bit SPIR-V words ready to be passed to
//   vkCreateShaderModule().  Returns an empty vector on compile/link error
//   and prints diagnostics via qWarning().
//
//   Compiling at runtime (rather than using pre-compiled .spv files) lets you
//   change shader source in C++ strings and rebuild without a separate
//   compilation step.
std::vector<uint32_t> compileGLSL(
    const std::string &source,
    VkShaderStageFlagBits stage
);
