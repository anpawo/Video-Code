// Runtime GLSL → SPIR-V compiler built on top of the glslang reference library.
// The entire compilation pipeline runs on the CPU at startup, producing a
// uint32_t array of SPIR-V words that Vulkan ingests via vkCreateShaderModule.
//
// SPIR-V cache
// ------------
// Compiled shaders are cached to disk so that warm starts skip glslang entirely.
// Cache key  : FNV-1a 64-bit hash of the GLSL source text (stable, no deps).
// Cache path : ~/.cache/video-code/spirv/v1/<hash>_<stage>.spv
// Invalidation: source text changes → different hash → automatic miss.
//              glslang ABI change  → bump the "v1" version prefix below.

#include "vulkan/ShaderCompiler.hpp"

#include <glslang/Public/ResourceLimits.h> // GetDefaultResources()
#include <glslang/Public/ShaderLang.h>     // glslang::TShader, TProgram
#include <glslang/SPIRV/GlslangToSpv.h>    // glslang::GlslangToSpv()

#include <QDebug>

#include <chrono>
#include <cstdlib>   // getenv
#include <filesystem>
#include <format>
#include <fstream>
#include <iostream>
#include <mutex>

namespace fs = std::filesystem;

// ─── SPIR-V cache helpers ────────────────────────────────────────────────────

// FNV-1a 64-bit — fast, stable, no dependencies.
// Same output on every platform/compiler/run for the same input bytes.
static uint64_t fnv1a64(const std::string& s)
{
    uint64_t h = 14695981039346656037ULL;
    for (unsigned char c : s)
        h = (h ^ c) * 1099511628211ULL;
    return h;
}

// Cache version prefix.  Increment when glslang's output format changes
// (e.g. after a major glslang upgrade) to auto-invalidate all old entries.
static constexpr const char* CACHE_VERSION = "v1";

static fs::path cacheDir()
{
    const char* home = getenv("HOME");
    fs::path dir = (home ? fs::path(home) : fs::temp_directory_path())
                   / ".cache" / "video-code" / "spirv" / CACHE_VERSION;
    fs::create_directories(dir);  // no-op if already exists
    return dir;
}

static fs::path cachePath(uint64_t hash, const char* stage)
{
    return cacheDir() / std::format("{:016x}_{}.spv", hash, stage);
}

// Read a cached .spv file.  Returns empty vector on any error (missing,
// truncated, not word-aligned — all treated as cache miss).
static std::vector<uint32_t> loadSPIRV(const fs::path& path)
{
    std::ifstream f(path, std::ios::binary | std::ios::ate);
    if (!f)
        return {};
    auto size = f.tellg();
    if (size <= 0 || size % 4 != 0)
        return {};
    f.seekg(0);
    std::vector<uint32_t> spirv(static_cast<size_t>(size) / 4);
    f.read(reinterpret_cast<char*>(spirv.data()), size);
    return f ? spirv : std::vector<uint32_t>{};
}

// Write compiled SPIR-V to disk.  Silently skips on write failure
// (bad cache dir permissions, disk full, etc.) — next launch will
// recompile and try again.
static void saveSPIRV(const fs::path& path, const std::vector<uint32_t>& spirv)
{
    std::ofstream f(path, std::ios::binary | std::ios::trunc);
    f.write(reinterpret_cast<const char*>(spirv.data()),
            static_cast<std::streamsize>(spirv.size() * 4));
}

// ─── glslang singleton ───────────────────────────────────────────────────────

// glslang::InitializeProcess() / FinalizeProcess() are process-scoped.
// Calling them once per compileGLSL() invocation (as the original code did)
// wastes ~394ms per call.  Use std::call_once so the first cache miss
// initializes glslang once and subsequent calls are a no-op.
static void ensureGLSLangInit()
{
    static std::once_flag s_flag;
    std::call_once(s_flag, [] { glslang::InitializeProcess(); });
}

// ─── stageToEsh ──────────────────────────────────────────────────────────────

// Converts a Vulkan shader stage flag to glslang's EShLanguage enum.
static EShLanguage stageToEsh(VkShaderStageFlagBits stage)
{
    switch (stage) {
        case VK_SHADER_STAGE_VERTEX_BIT:   return EShLangVertex;
        case VK_SHADER_STAGE_FRAGMENT_BIT: return EShLangFragment;
        case VK_SHADER_STAGE_GEOMETRY_BIT: return EShLangGeometry;
        default:                           return EShLangVertex;
    }
}

// ─── compileGLSL ─────────────────────────────────────────────────────────────

// Full pipeline: GLSL source text → (cache lookup) → SPIR-V words.
// On a cache hit the function returns in < 1ms without touching glslang.
// On a cache miss it compiles, caches the result, then returns.
std::vector<uint32_t> compileGLSL(const std::string& source, VkShaderStageFlagBits stage)
{
    using Clock = std::chrono::high_resolution_clock;
    using Ms    = std::chrono::duration<double, std::milli>;
    auto _t0    = Clock::now();

    const char* stageName = (stage == VK_SHADER_STAGE_VERTEX_BIT)   ? "vert"
                          : (stage == VK_SHADER_STAGE_FRAGMENT_BIT) ? "frag"
                                                                     : "geom";

    // ── Cache lookup ──────────────────────────────────────────────────────────
    uint64_t    hash = fnv1a64(source);
    fs::path    path = cachePath(hash, stageName);
    auto        hit  = loadSPIRV(path);
    if (!hit.empty()) {
        double ms = std::chrono::duration_cast<Ms>(Clock::now() - _t0).count();
        std::cout << std::format("[startup] compileGLSL({:4s}): {:6.1f}ms  ({} words)  [cache hit]\n",
                                 stageName, ms, hit.size());
        return hit;
    }

    // ── Cache miss: compile ───────────────────────────────────────────────────
    // InitializeProcess is called once for the process lifetime.
    // ~394ms on first call; subsequent calls are a no-op (std::call_once).
    ensureGLSLangInit();

    EShLanguage lang = stageToEsh(stage);

    glslang::TShader shader(lang);
    const char* src = source.c_str();
    shader.setStrings(&src, 1);

    shader.setEnvInput(glslang::EShSourceGlsl, lang, glslang::EShClientVulkan, 100);
    shader.setEnvClient(glslang::EShClientVulkan, glslang::EShTargetVulkan_1_0);
    shader.setEnvTarget(glslang::EShTargetSpv, glslang::EShTargetSpv_1_0);

    if (!shader.parse(GetDefaultResources(), 100, false, EShMsgDefault)) {
        qWarning("GLSL compile error: %s", shader.getInfoLog());
        return {};
    }

    glslang::TProgram program;
    program.addShader(&shader);
    if (!program.link(EShMsgDefault)) {
        qWarning("GLSL link error: %s", program.getInfoLog());
        return {};
    }

    std::vector<uint32_t> spirv;
    glslang::GlslangToSpv(*program.getIntermediate(lang), spirv);

    // FinalizeProcess() intentionally omitted — process-scoped, OS reclaims.

    // ── Persist to cache ──────────────────────────────────────────────────────
    saveSPIRV(path, spirv);

    double ms = std::chrono::duration_cast<Ms>(Clock::now() - _t0).count();
    std::cout << std::format("[startup] compileGLSL({:4s}): {:6.1f}ms  ({} words)  [compiled + cached]\n",
                             stageName, ms, spirv.size());

    return spirv;
}
