/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Compiler
*/

#include "compiler/Compiler.hpp"

VC::Compiler::Compiler(const argparse::ArgumentParser &parser)
    : _core(parser)
{
}

VC::Compiler::~Compiler() = default;

int VC::Compiler::generateVideo()
{
    return _core.generateVideo();
}
