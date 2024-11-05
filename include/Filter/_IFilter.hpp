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
     * @brief sets the arguments you will use in the command. to each it's own.
     */
    virtual IFilter& set() = 0;

    /**
     * @brief return the formatted command string.
     */
    virtual std::string getCommand(const std::vector<std::string>& defaultInputStreams, const std::vector<std::string>& newInputStreams) = 0;

    /**
     * @brief return the new input streams created by the complex filter.
     */
    virtual std::string getNewInputs() = 0;

private:
};
