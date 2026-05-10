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
                msg = std::format("{}[CREATE]:{}{}[{}]:{} {}", Color::CYAN, Color::RESET, Color::CYAN, s["type"].get<std::string>(), Color::RESET, s["args"].dump());
            } else if (action == "Apply") {
                msg = std::format("{}[APPLY]:[{}]:[{}]:{} {}", Color::MAGENTA, s["name"].get<std::string>(), s["input"].get<int>(), Color::RESET, s["args"].dump());
            } else if (action == "Wait") {
                msg = std::format("{}[WAIT]:{}{}", Color::MAGENTA, Color::RED, s["n"].get<int>());
            } else if (action == "Timestamp") {
                msg = std::format("{}[TIMESTAMP]:{} {}  at frame {}", Color::GREEN, Color::RESET, s["name"].get<std::string>(), s["time"].get<size_t>());
            } else {
                msg = s.dump();
            }

            log(msg);
        }
    };

    inline Logger Debug{"Debug", Color::CYAN};
}
