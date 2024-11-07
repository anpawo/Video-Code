/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Overlay
*/

#pragma once

#include <string>
#include <vector>

#include "Filter/_AFilter.hpp"

class Overlay final : public AFilter {
public:

    Overlay(std::string&& stream0, std::string&& stream1, std::string&& output)
        : AFilter(
              std::forward<std::string>(stream0),
              std::forward<std::string>(stream1),
              std::forward<std::string>(output)
          ) {}

    ~Overlay() = default;

    Overlay set(int x, int y)
    {
        _overlayX = x;
        _overlayY = y;
        return *this;
    }

    std::string getCommand(const std::vector<Input>& defaultInputStreams, const std::vector<std::string>& newInputStreams)
    {
        const std::string s0 = getInputName(defaultInputStreams, newInputStreams, _stream0);
        const std::string s1 = getInputName(defaultInputStreams, newInputStreams, _stream1);

        return s0 + s1 + _name + std::to_string(_overlayX) + ":" + std::to_string(_overlayY) + "[" + _output + "];";
    }

private:

    std::string _name{"overlay="};

    int _overlayX;
    int _overlayY;
};
