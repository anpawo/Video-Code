/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Logger
*/

#pragma once

#include <format>
#include <iostream>
#include <nlohmann/json.hpp>
#include <string>

// VC_TIME(label, block) — times a block and prints; compiles to just `block` in release.
// VC_LOG(msg)           — prints a debug line; compiles to nothing in release.
// VC_SLOG(msg)          — startup/perf diagnostic print; gated on VC_VERBOSE.
//                         Silent by default in release. Enable with -DVC_VERBOSE.
#ifdef VC_VERBOSE
    #define VC_SLOG(msg) (std::cout << (msg))
#else
    #define VC_SLOG(msg) ((void)0)
#endif

#ifdef VC_DEBUG_ON
    #include <chrono>
    #define VC_TIME(label, block)                                                                                                                    \
        do {                                                                                                                                         \
            auto _vc_t0 = std::chrono::high_resolution_clock::now();                                                                                 \
            block;                                                                                                                                   \
            auto _vc_t1 = std::chrono::high_resolution_clock::now();                                                                                 \
            std::cout << std::format("[timer] {}: {}ms\n", (label), std::chrono::duration_cast<std::chrono::milliseconds>(_vc_t1 - _vc_t0).count()); \
        } while (0)
    #define VC_LOG(msg) (std::cout << (msg))
#else
    #define VC_TIME(label, block) block
    #define VC_LOG(msg) ((void)0)
#endif

namespace VC
{
    namespace Color
    {
        constexpr const char* CYAN = "\033[36m";
        constexpr const char* RED = "\033[31m";
        constexpr const char* GREEN = "\033[32m";
        constexpr const char* MAGENTA = "\033[35m";
        constexpr const char* RESET = "\033[0m";
    }

    struct Logger
    {
        const std::string prefix;
        const char*       color;
        std::ostream&     out;

        Logger(std::string prefix, const char* color, std::ostream& out = std::cout)
            : prefix(std::move(prefix)), color(color), out(out)
        {
        }

        template <typename T>
        void log(const T& msg) const
        {
            out << msg << "\n";
        }

        void logStack(const nlohmann::json& s) const
        {
            std::string action = s["action"];
            std::string msg;

            if (action == "Create") {
                msg = std::format("{}[CREATE]{} {}[{}]{} {}", Color::CYAN, Color::RESET, Color::CYAN, s["type"].get<std::string>(), Color::RESET, truncateArgs(s["args"]).dump());
            } else if (action == "Apply") {
                msg = std::format("{}[APPLY]{} [{}] [{}] {}", Color::MAGENTA, Color::RESET, s["name"].get<std::string>(), s["input"].get<int>(), truncateArgs(s["args"]).dump());
            } else if (action == "Wait") {
                msg = std::format("{}[WAIT]{} {}{}{}", Color::MAGENTA, Color::RESET, Color::RED, s["n"].get<int>(), Color::RESET);
            } else if (action == "Timestamp") {
                msg = std::format("{}[TIMESTAMP]{} {}  at frame {}", Color::GREEN, Color::RESET, s["name"].get<std::string>(), s["time"].get<size_t>());
            } else {
                msg = s.dump();
            }

            log(msg);
        }

    private:

        static std::string truncateVal(const std::string& s)
        {
            size_t n = 30;

            if (s.size() > n)
                return s.substr(0, n) + "...";
            return s;
        }

        static nlohmann::json truncateArgs(nlohmann::json j)
        {
            if (j.is_string())
                return truncateVal(j.get<std::string>());
            if (j.is_array()) {
                if (j.dump().size() > 20) {
                    std::string repr = "[";
                    size_t      n = std::min(j.size(), size_t(3));
                    for (size_t i = 0; i < n; i++) {
                        if (i > 0) repr += ", ";
                        repr += j[i].dump();
                    }
                    repr += ", ...]";
                    return repr;
                }
            } else if (j.is_object()) {
                for (auto& [k, v] : j.items())
                    v = truncateArgs(v);
            }
            return j;
        }
    };

    inline Logger Debug{"Debug", Color::CYAN};
}
