#pragma once

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
    inline std::string resourceDir(const char* baked, const char* shipped)
    {
        const std::filesystem::path beside = executableDir() / shipped;
        return std::filesystem::is_directory(beside) ? beside.string() : std::string(baked);
    }
} // namespace VC
