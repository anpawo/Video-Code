/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Command
*/

#pragma once

#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "Filter/_IFilter.hpp"

class CommandFactory {
public:

    CommandFactory() = default;
    ~CommandFactory() = default;

    void map(const std::string &&streamName);

    template <typename... Args>
    typename std::enable_if<(std::is_constructible<std::string, Args>::value && ...), void>::type
    addInput(Args &&...args)
    {
        _inputs.emplace_back(std::forward<Args>(args)...);
    }

    template <typename... Filters>
    void addFilter(Filters &&...filters)
    {
        (_filters.emplace_back(std::make_unique<Filters>(std::forward<Filters>(filters))), ...);
    }

    void runCommand();

    std::vector<std::unique_ptr<IFilter>> _filters;

private:

    std::vector<std::string> _inputs;
};

// array of command and params
