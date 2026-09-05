/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** ScreenSize
*/

#include "core/ScreenSize.hpp"

#include <pybind11/embed.h>

#include <argparse/argparse.hpp>
#include <filesystem>
#include <format>
#include <iostream>

#include "input/Metadata.hpp"

namespace py = pybind11;

namespace
{
    // The shapes --for knows, by the name of the place the film is watched
    // rather than by its pixels: what an author picks is a destination, and
    // 1080x1920 is a consequence of it. A shape is a RESOLUTION and nothing
    // else — the scene runs again inside it and lays itself out (Split.AUTO,
    // W/H, TOP_SIDE...), so nothing here crops or scales anything.
    struct Shape
    {
        const char *name;
        float       width;
        float       height;
    };

    constexpr Shape kShapes[] = {
        {"youtube", 1920.f, 1080.f},
        {"tiktok", 1080.f, 1920.f},
        {"square", 1080.f, 1080.f},
    };

    std::string shapeNames()
    {
        std::string list;
        for (const Shape &s : kShapes)
            list += (list.empty() ? "" : ", ") + std::string(s.name);
        return list;
    }

    // "out/film.mp4" + "tiktok" -> "out/film-tiktok.mp4". The shape has to be
    // in the NAME: three renders of one command otherwise overwrite each other,
    // and the survivor says nothing about which one it is.
    std::string named(const std::string &path, const std::string &shape)
    {
        const std::filesystem::path out(path);
        return (out.parent_path() / std::format("{}-{}{}", out.stem().string(), shape, out.extension().string())).string();
    }
}

void VC::applyScreenSize(float width, float height)
{
    config::screen = {width, height};
    config::screenOffset = {width / 2.f, height / 2.f};

    // How Python learns the resolution: constants.py reads this at import time
    // and builds the world box from it. os.environ also putenv()s, so it
    // survives into anything the scene shells out to.
    try {
        py::module_::import("os").attr("environ")["VC_SCREEN"] =
            std::format("{}x{}", (int)width, (int)height);

        // Too late for the import-time read if the package is already loaded —
        // which happens when one process renders several sizes in a row (the
        // visual-regression suite). Then, and only then, re-derive in place.
        py::dict modules = py::module_::import("sys").attr("modules");
        if (modules.contains("videocode.constants"))
            modules["videocode.constants"].attr("setScreen")(int(width), int(height));
    } catch (const py::error_already_set &e) {
        std::cerr << "Could not export VC_SCREEN:\n"
                  << e.what() << "\n";
    }
}

Config VC::makeConfig(const argparse::ArgumentParser &parser)
{
    // The resolution comes from the command line and nowhere else — a scene
    // cannot change it. Python is TOLD the answer (applyScreenSize), never
    // asked for it, which keeps the world box, the preview surface and the
    // encoder on the same numbers by construction.
    const float width = parser.get<float>("--width");
    const float height = parser.get<float>("--height");

    if (width < 2.f || height < 2.f) {
        std::cerr << "Invalid resolution " << (int)width << "x" << (int)height << ".\n";
        std::exit(EXIT_FAILURE);
    }
    if ((int)width % 2 != 0 || (int)height % 2 != 0)
        std::cerr << "Warning: " << (int)width << "x" << (int)height
                  << " has an odd dimension — H.264/VP9 encoding will fail. Use even values.\n";

    applyScreenSize(width, height);

    return Config{
        .screenWidth = width,
        .screenHeight = height,

        .windowRatio = parser.get<float>("--windowRatio"),

        .framerate = parser.get<int>("--framerate"),

        .hwEncode = parser.get<bool>("--hwencode"),

        .sourceFile = parser.get("--file"),
        .outputFile = parser.get("--generate"),

        .renderFrom = parser.present("--from").value_or(""),
        .renderTo = parser.present("--to").value_or(""),

        .sheetTiles = parser.present<int>("--sheet").value_or(1),
    };
}

std::vector<Config> VC::makeConfigs(const argparse::ArgumentParser &parser)
{
    const Config      base = makeConfig(parser);
    const std::string asked = parser.present("--for").value_or("");

    if (asked.empty())
        return {base};

    // The shapes decide the size, so the size flags cannot also. Said rather
    // than resolved quietly: `-w 800 --for tiktok` is a person expecting one
    // of the two to win, and silence would let them believe it was theirs.
    if (parser.is_used("--width") || parser.is_used("--height"))
        std::cerr << "video-code: --for decides the resolution — the --width/--height you gave are not used.\n";

    std::vector<Config> configs;
    for (size_t start = 0; start <= asked.size();) {
        const size_t      comma = std::min(asked.find(',', start), asked.size());
        const size_t      from = asked.find_first_not_of(" \t", start);
        const size_t      to = asked.find_last_not_of(" \t", comma - 1);
        const std::string name = (from == std::string::npos || from >= comma) ? "" : asked.substr(from, to - from + 1);
        start = comma + 1;

        const Shape *shape = nullptr;
        for (const Shape &candidate : kShapes)
            if (name == candidate.name)
                shape = &candidate;
        if (!shape) {
            std::cerr << std::format("video-code: --for does not know the shape \"{}\". It knows {}.\n", name, shapeNames());
            std::exit(EXIT_FAILURE);
        }

        Config config = base;
        config.screenWidth = shape->width;
        config.screenHeight = shape->height;
        config.windowWidth = config.screenWidth * config.windowRatio;
        config.windowHeight = config.screenHeight * config.windowRatio;
        config.outputFile = named(base.outputFile, name);
        config.shapeNote = name;
        configs.push_back(config);
    }

    // Numbered only when there is a run to be somewhere in.
    if (configs.size() > 1)
        for (size_t i = 0; i < configs.size(); ++i)
            configs[i].shapeNote += std::format(", {} of {}", i + 1, configs.size());
    return configs;
}
