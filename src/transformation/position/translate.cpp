/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** translate
*/

#include <memory>

#include "input/IInput.hpp"
#include "transformation/transformation.hpp"

void transformation::translate(std::shared_ptr<IInput> input, [[maybe_unused]] Register &reg, const json::object_t &args)
{
    int x = args.at("x");
    int y = args.at("y");

    for (auto &[_, meta] : *input)
    {
        meta.x = x;
        meta.y = y;
    }
}
