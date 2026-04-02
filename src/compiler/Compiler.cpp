/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Compiler
*/

#include "compiler/Compiler.hpp"

VC::Compiler::Compiler(const argparse::ArgumentParser &parser)
    : config({
          .screenWidth = parser.get<float>("--width"),
          .screenHeight = parser.get<float>("--height"),

          .framerate = parser.get<int>("--framerate"),

          .sourceFile = parser.get("--file"),
          .outputFile = parser.get("--generate"),
      })
    , _core(parser, config)
{
}

VC::Compiler::~Compiler() = default;

int VC::Compiler::generateVideo()
{
    return _core.generateVideo();
}
