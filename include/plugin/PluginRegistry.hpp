/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Plugin registry
*/

#pragma once

#include <filesystem>
#include <map>
#include <memory>
#include <nlohmann/json.hpp>
#include <string>
#include <vector>

#include "plugin/PluginAPI.hpp"

namespace VC
{
    class PluginRegistry
    {
    public:

        void registerInput(const std::string& name, InputFactoryFunction factory);
        void registerFragmentShader(const std::string& name, FragmentShaderFactoryFunction factory);

        std::unique_ptr<IInput> createInput(const std::string& name, nlohmann::json::object_t&& args) const;
        std::unique_ptr<IFragmentShader> createFragmentShader(const std::string& name, const nlohmann::json::object_t& args) const;

        void loadPluginDirectories(const std::vector<std::string>& directories);

    private:

        void loadMetadataFile(const std::filesystem::path& metadataPath);
        void loadCppPlugin(const std::filesystem::path& metadataPath, const std::filesystem::path& libraryPath);

        std::map<std::string, InputFactoryFunction> _inputFactories{};
        std::map<std::string, FragmentShaderFactoryFunction> _shaderFactories{};
        std::vector<void*> _libraryHandles{};
    };
}
