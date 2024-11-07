/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** _InterfaceFilterComplex
*/

#pragma once

#include <string>
#include <vector>

#include "Input.hpp"

class IFilter {
public:

    IFilter() = default;
    virtual ~IFilter() = default;

    /**
     * @brief return the formatted command string.
     */
    virtual std::string getCommand(const std::vector<Input>& defaultInputStreams, const std::vector<std::string>& newInputStreams) = 0;

    /**
     * @brief return the new input streams created by the complex filter.
     */
    virtual std::string getNewInputs() = 0;

    /**
     * @brief return some additional args if any needed by the complex filter.
     */
    virtual std::string getAdditionalArgs() = 0;

    /**
     * @brief return the stream name.
     */
    virtual const std::string& getStream0() const = 0;
    virtual const std::string& getStream1() const = 0;

    /**
     * @brief set the stream name.
     */
    virtual void setStream0(const std::string& value) = 0;
    virtual void setStream1(const std::string& value) = 0;

private:
};
