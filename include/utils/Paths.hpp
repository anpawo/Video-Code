#pragma once

#include <unistd.h>

#include <cstdlib>
#include <filesystem>
#include <string>
#ifdef __APPLE__
    #include <mach-o/dyld.h>
#endif

namespace VC
{
    // Where the running executable sits — without Qt, because the first
    // resource asked for is a shader, and that can happen before any
    // QCoreApplication exists.
    inline std::filesystem::path executableDir()
    {
#ifdef __APPLE__
        char     buffer[4096];
        uint32_t size = sizeof buffer;
        if (_NSGetExecutablePath(buffer, &size) == 0)
            return std::filesystem::weakly_canonical(buffer).parent_path();
#else
        std::error_code ec;
        const auto      self = std::filesystem::read_symlink("/proc/self/exe", ec);
        if (!ec)
            return self.parent_path();
#endif
        return std::filesystem::current_path();
    }

    // A resource read at runtime lives beside the executable when it was
    // shipped there, else where the build baked it. A copied folder stands on
    // its own; a checkout keeps editing in place, reload and all.
    // The socket this editor answers `tell` on — its own, by pid, so two open
    // editors never answer each other's calls — and the well-known name that
    // points at whichever opened last, which is what a terminal reaches for.
    // VC_SOCKET names both, for a test that must not touch yours.
    inline std::string latestSocketPath() { return "/tmp/videocode-editor.sock"; }

    inline std::string ownSocketPath()
    {
        if (const char* named = std::getenv("VC_SOCKET"); named && *named)
            return named;
        return "/tmp/videocode-editor-" + std::to_string(getpid()) + ".sock";
    }

    inline std::string resourceDir(const char* baked, const char* shipped)
    {
        const std::filesystem::path beside = executableDir() / shipped;
        return std::filesystem::is_directory(beside) ? beside.string() : std::string(baked);
    }
} // namespace VC
