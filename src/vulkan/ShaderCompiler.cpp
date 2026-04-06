// Runtime GLSL → SPIR-V compiler built on top of the glslang reference library.
// The entire compilation pipeline runs on the CPU at startup, producing a
// uint32_t array of SPIR-V words that Vulkan ingests via vkCreateShaderModule.

#include "vulkan/ShaderCompiler.hpp"

#include <glslang/Public/ResourceLimits.h> // GetDefaultResources() — hardware limits
#include <glslang/Public/ShaderLang.h>     // glslang::TShader, TProgram
#include <glslang/SPIRV/GlslangToSpv.h>    // glslang::GlslangToSpv()

#include <QDebug>

// stageToEsh
//   Converts a Vulkan shader stage flag to glslang's own EShLanguage enum.
//   glslang predates Vulkan and uses its own type system internally.
static EShLanguage stageToEsh(VkShaderStageFlagBits stage)
{
    switch (stage) {
        case VK_SHADER_STAGE_VERTEX_BIT:
            return EShLangVertex;
        case VK_SHADER_STAGE_FRAGMENT_BIT:
            return EShLangFragment;
        case VK_SHADER_STAGE_GEOMETRY_BIT:
            return EShLangGeometry;
        default:
            return EShLangVertex;
    }
}

// compileGLSL
//   Full pipeline: GLSL source text → parsed AST → linked program → SPIR-V words.
std::vector<uint32_t> compileGLSL(const std::string &source, VkShaderStageFlagBits stage)
{
    // glslang uses a global process state; must be initialised before any
    // shader object is created and finalised when done to release resources.
    glslang::InitializeProcess();

    EShLanguage lang = stageToEsh(stage);

    // TShader holds the source and compilation state for one shader stage.
    glslang::TShader shader(lang);

    const char *src = source.c_str();
    shader.setStrings(&src, 1); // Accept an array of source strings (here just one).

    // Tell glslang the dialect and target platform:
    //   - Input language : GLSL (as opposed to HLSL)
    //   - Client         : Vulkan (affects built-in variable semantics)
    //   - Target API ver : Vulkan 1.0
    //   - SPIR-V version : 1.0  (compatible with Vulkan 1.0)
    shader.setEnvInput(glslang::EShSourceGlsl, lang, glslang::EShClientVulkan, 100);
    shader.setEnvClient(glslang::EShClientVulkan, glslang::EShTargetVulkan_1_0);
    shader.setEnvTarget(glslang::EShTargetSpv, glslang::EShTargetSpv_1_0);

    // Parse: tokenise, build AST, type-check.
    // GetDefaultResources() supplies conservative hardware limits (max texture
    // units, max uniform components, etc.) so the compiler can validate usage.
    if (!shader.parse(GetDefaultResources(), 100, false, EShMsgDefault)) {
        qWarning("GLSL compile error: %s", shader.getInfoLog());
        glslang::FinalizeProcess();
        return {};
    }

    // Link: resolve cross-stage interfaces (outputs of vertex must match
    // inputs of fragment, etc.).  Required even for a single shader stage.
    glslang::TProgram program;
    program.addShader(&shader);
    if (!program.link(EShMsgDefault)) {
        qWarning("GLSL link error: %s", program.getInfoLog());
        glslang::FinalizeProcess();
        return {};
    }

    // Code-generate: walk the linked IR and emit SPIR-V words.
    // getIntermediate(lang) returns the IR for the requested stage.
    std::vector<uint32_t> spirv;
    glslang::GlslangToSpv(*program.getIntermediate(lang), spirv);

    glslang::FinalizeProcess();
    return spirv; // Ready for vkCreateShaderModule().
}
