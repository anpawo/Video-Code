/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** translate
*/

#include <memory>

#include "transformation/transformation.hpp"
#include "vm/Register.hpp"

void transformation::repeat(std::shared_ptr<IInput> input, [[maybe_unused]] Register &reg, const json::object_t &args)
{
    input->repeat(args.at("n"));
}
