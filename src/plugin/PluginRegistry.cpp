/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** Plugin registry
*/

#include "plugin/PluginRegistry.hpp"

#include <dlfcn.h>

#include <fstream>
#include <iostream>

#include "utils/Exception.hpp"

using json = nlohmann::json;

namespace
{
    void registerInputThunk(void* context, const char* name, VC::InputFactoryFunction factory)
    {
        auto* registry = static_cast<VC::PluginRegistry*>(context);
        registry->registerInput(name, factory);
    }

    void registerFragmentShaderThunk(void* context, const char* name, VC::FragmentShaderFactoryFunction factory)
    {
        auto* registry = static_cast<VC::PluginRegistry*>(context);
        registry->registerFragmentShader(name, factory);
    }
}

void VC::PluginRegistry::registerInput(const std::string& name, InputFactoryFunction factory)
{
    _inputFactories[name] = factory;
}

void VC::PluginRegistry::registerFragmentShader(const std::string& name, FragmentShaderFactoryFunction factory)
{
    _shaderFactories[name] = factory;
}

std::unique_ptr<IInput> VC::PluginRegistry::createInput(const std::string& name, json::object_t&& args) const
{
    auto found = _inputFactories.find(name);

    if (found == _inputFactories.end()) {
        throw Error("No input plugin registered for type: " + name);
    }

    return found->second(std::move(args));
}

std::unique_ptr<IFragmentShader> VC::PluginRegistry::createFragmentShader(const std::string& name, const json::object_t& args) const
{
    auto found = _shaderFactories.find(name);

    if (found == _shaderFactories.end()) {
        throw Error("No fragment shader plugin registered for type: " + name);
    }

    return found->second(args);
}

void VC::PluginRegistry::loadPluginDirectories(const std::vector<std::string>& directories)
{
    for (const auto& directory : directories) {
        std::filesystem::path base(directory);

        if (!std::filesystem::exists(base)) {
            continue;
        }

        for (const auto& entry : std::filesystem::recursive_directory_iterator(base)) {
            if (!entry.is_regular_file()) {
                continue;
            }

            if (entry.path().extension() == ".json") {
                loadMetadataFile(entry.path());
            }
        }
    }
}

void VC::PluginRegistry::loadMetadataFile(const std::filesystem::path& metadataPath)
{
    std::ifstream metadataFile(metadataPath);

    if (!metadataFile.is_open()) {
        throw Error("Could not open plugin metadata: " + metadataPath.string());
    }

    json metadata = json::parse(metadataFile);

    const auto cppRelativePath = metadata.at("cpp_library").get<std::string>();
    std::filesystem::path cppLibraryPath = metadataPath.parent_path() / cppRelativePath;

    loadCppPlugin(metadataPath, cppLibraryPath);
}

void VC::PluginRegistry::loadCppPlugin(const std::filesystem::path& metadataPath, const std::filesystem::path& libraryPath)
{
    if (!std::filesystem::exists(libraryPath)) {
        throw Error("Plugin C++ library not found: " + libraryPath.string() + " (metadata: " + metadataPath.string() + ")");
    }

    void* handle = dlopen(libraryPath.c_str(), RTLD_NOW);

    if (handle == nullptr) {
        throw Error("dlopen failed for plugin: " + libraryPath.string() + " => " + dlerror());
    }

    auto registerFn = reinterpret_cast<VCRegisterPluginFunction>(dlsym(handle, "vc_register_plugin"));

    if (registerFn == nullptr) {
        dlclose(handle);
        throw Error("Plugin is missing vc_register_plugin symbol: " + libraryPath.string());
    }

    VC::PluginRegistrar registrar{
        .context = this,
        .registerInput = registerInputThunk,
        .registerFragmentShader = registerFragmentShaderThunk,
    };

    registerFn(&registrar);
    _libraryHandles.push_back(handle);
}
