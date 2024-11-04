/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Concatenate
*/

#pragma once

#include <string>
#include <vector>

#include "Filter/_AFilter.hpp"

class Concatenate final : public AFilterComplex {
public:

    Concatenate() = default;
    ~Concatenate() = default;

    std::string getCommand() { return "concatenate"; }

    std::vector<std::string> getNewInputs() { return {}; }

protected:
private:
};
