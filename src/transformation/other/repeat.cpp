/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** translate
*/

#include "transformation/transformation.hpp"
#include "vm/Register.hpp"

void transformation::repeat(IterableInput input, const json::object_t& args)
{
    input.get()->repeat(args.at("n"));
}
