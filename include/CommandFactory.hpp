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
#include "Input.hpp"
#include "Utils/Vector.hpp"

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

    template <typename T>
    T &applyAlias(T &filter)
    {
        try {
            auto index = findIndexOrThrow(_defaultInputStreams, filter.getStream0());
            filter.setStream0(_defaultInputStreams[index].getAlias());
        } catch (const Error &) {
        }

        if (filter.getStream1() != "") {
            try {
                auto index = findIndexOrThrow(_defaultInputStreams, filter.getStream1());
                filter.setStream1(_defaultInputStreams[index].getAlias());
            } catch (const Error &) {
            }
        }
        return filter;
    }

    template <typename... Filters>
    void addFilters(Filters &&...filters)
    {
        (_filters.emplace_back(std::make_unique<Filters>(std::forward<Filters>(applyAlias(filters)))), ...);
    }

    std::string generateCommand(std::string &&outputFile)
    {
        std::string cmd = "ffmpeg -y"; ///> Override file

        // Inputs
        for (const auto &it : _defaultInputStreams) {
            cmd += " -i " + it.getFilename();
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
    std::vector<Input> _defaultInputStreams{};
    std::vector<std::string> _newInputStreams{};
};

// array of command and params
