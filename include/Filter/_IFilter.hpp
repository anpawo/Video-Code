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
    virtual std::string getCommand() = 0;

    /**
     * @brief return the new input streams created by the complex filter.
     */
    virtual std::vector<std::string> getNewInputs() = 0;

private:
};
