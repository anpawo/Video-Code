/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** _InterfaceFilterComplex
*/

#pragma once

#include <string>
#include <vector>

class IFilter {
public:

    IFilter() = default;
    virtual ~IFilter() = default;

    /**
     * @brief return the formatted command string.
     */
    virtual std::string getCommand(const std::vector<std::string>& defaultInputStreams, const std::vector<std::string>& newInputStreams) = 0;

    /**
     * @brief return the new input streams created by the complex filter.
     */
    virtual std::string getNewInputs() = 0;

    /**
     * @brief return some additional args if any needed by the complex filter.
     */
    virtual std::string getAdditionalArgs() = 0;

private:
};
