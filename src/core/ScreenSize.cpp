/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** ScreenSize
*/

#include "core/ScreenSize.hpp"

#include <pybind11/embed.h>

#include <argparse/argparse.hpp>
#include <format>
#include <iostream>

#include "input/Metadata.hpp"

namespace py = pybind11;

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
    };
}
