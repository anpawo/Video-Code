/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Command
*/

#pragma once

#include <cstdlib>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "Filter/_IFilter.hpp"

/**
 * @brief This class will only handle video streams.
 */
class CommandFactory {
public:

    CommandFactory() = default;
    ~CommandFactory() = default;

    template <typename... Strings>
    void addInputs(Strings &&...strings)
    {
        (_defaultInputStreams.emplace_back(std::forward<Strings>(strings)), ...);
    }

    template <typename... Filters>
    void addFilters(Filters &&...filters)
    {
        (_filters.emplace_back(std::make_unique<Filters>(std::forward<Filters>(filters))), ...);
    }

    std::string generateCommand(std::string &&outputFile)
    {
        std::string cmd = "ffmpeg -y"; ///> Override file

        // Inputs
        for (const auto &it : _defaultInputStreams) {
            cmd += " -i " + it;
        }

        // Filters
        cmd += " -filter_complex \"";
        for (const auto &filter : _filters) {
            cmd += filter->getCommand(_defaultInputStreams, _newInputStreams);
            _newInputStreams.emplace_back(filter->getNewInputs());
        }
        cmd += "\"";

        // Map last created stream
        cmd += " -map \"[" + _newInputStreams.back() + "]\"";

        // Add additional parameters if the last commands needs any (extract a single frame)
        cmd += _filters.back()->getAdditionalArgs();

        // Output filename
        cmd += " " + outputFile;

        return cmd;
    }

    void generateOutput(std::string &&outputFile)
    {
        system(generateCommand(std::forward<std::string>(outputFile)).c_str());
    }

private:

    std::vector<std::unique_ptr<IFilter>> _filters;
    std::vector<std::string> _defaultInputStreams{};
    std::vector<std::string> _newInputStreams{};
};

// array of command and params
