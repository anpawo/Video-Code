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

    virtual const std::string& getStream0() const
    {
        return _stream0;
    }

    virtual const std::string& getStream1() const
    {
        return _stream1;
    }

    virtual void setStream0(const std::string& value)
    {
        _stream0 = value;
    }

    virtual void setStream1(const std::string& value)
    {
        _stream1 = value;
    }

protected:

    const std::string getInputName(const std::vector<Input>& defaultInputStreams, const std::vector<std::string>& newInputStreams, const std::string& streamName) const
    {
        try {
            return "[" + std::to_string(findIndexOrThrow(defaultInputStreams, streamName)) + ":v:0]";
        } catch (const Error&) {
            findOrThrow(newInputStreams, streamName);
            return "[" + streamName + "]";
        }
    }

    std::string _stream0;
    std::string _stream1;
    std::string _output;
};
