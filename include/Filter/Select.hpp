/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Select
*/

#pragma once

#include <string>
#include <vector>

#include "Filter/_AFilter.hpp"

class Select final : public AFilter {
public:

    Select(std::string&& stream0, std::string&& output)
        : AFilter(
              std::forward<std::string>(stream0),
              "",
              std::forward<std::string>(output)
          ) {}

    ~Select() = default;

    Select set(std::size_t frameIndex)
    {
        _frameIndex = frameIndex;
        return *this;
    }

    std::string getCommand(const std::vector<std::string>& defaultInputStreams, const std::vector<std::string>& newInputStreams)
    {
        const std::string s = getInputName(defaultInputStreams, newInputStreams, _stream0);

        return s + _name + "=eq(n\\," + std::to_string(_frameIndex) + ")[" + _output + "];";
    }

    std::string getAdditionalArgs()
    {
        return " -frames:v 1 -update 1";
    }

private:

    std::string _name{"select"};
    std::size_t _frameIndex;
};
