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

class Concatenate final : public AFilter {
public:

    Concatenate(std::string&& stream0, std::string&& stream1, std::string&& output)
        : AFilter(
              std::forward<std::string>(stream0),
              std::forward<std::string>(stream1),
              std::forward<std::string>(output)
          ) {}

    ~Concatenate() = default;

    std::string getCommand(const std::vector<std::string>& defaultInputStreams, const std::vector<std::string>& newInputStreams)
    {
        const std::string s0 = getInputName(defaultInputStreams, newInputStreams, _stream0);
        const std::string s1 = getInputName(defaultInputStreams, newInputStreams, _stream1);

        return s0 + s1 + _name + _metadata + "[" + _output + "];";
    }

private:

    std::string _name{"concat"};
    std::string _metadata{"=n=2:v=1"};
};
