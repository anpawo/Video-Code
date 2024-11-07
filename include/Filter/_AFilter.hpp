/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** _AFilterComplex
*/

#pragma once

#include "Filter/_IFilter.hpp"
#include "Utils/Vector.hpp"

class AFilter : public IFilter {
public:

    AFilter(std::string&& stream0, std::string&& stream1, std::string&& output) : _stream0(stream0), _stream1(stream1), _output(output) {}

    virtual ~AFilter() = default;

    virtual std::string getNewInputs()
    {
        return _output;
    }

    virtual std::string getAdditionalArgs()
    {
        return "";
    }

protected:

    const std::string getInputName(const std::vector<std::string>& defaultInputStreams, const std::vector<std::string>& newInputStreams, const std::string& streamName) const
    {
        try {
            return "[" + std::to_string(findIndex(defaultInputStreams, streamName)) + ":v:0]";
        } catch (const Error&) {
            find(newInputStreams, streamName);
            return "[" + streamName + "]";
        }
    }

    std::string _stream0;
    std::string _stream1;
    std::string _output;
};
