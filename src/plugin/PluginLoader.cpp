/**
 * @file PluginLoader.cpp
 * @brief Implementation of plugin loading system
 */

#include "plugin/PluginLoader.hpp"
#include <dlfcn.h>
#include <fstream>
#include <iostream>

namespace vc {

// ============================================================================
// PluginRegistry Implementation
// ============================================================================

PluginRegistry& PluginRegistry::getInstance() {
    static PluginRegistry instance;
    return instance;
}

void PluginRegistry::registerTransformation(const std::string& name, 
                                            const PluginMetadata& metadata) {
    transformation_plugins_[name] = metadata;
}

void PluginRegistry::registerInput(const std::string& name, 
                                   const PluginMetadata& metadata) {
    input_plugins_[name] = metadata;
}

const PluginMetadata* PluginRegistry::getTransformation(const std::string& name) const {
    auto it = transformation_plugins_.find(name);
    return (it != transformation_plugins_.end()) ? &it->second : nullptr;
}

const PluginMetadata* PluginRegistry::getInput(const std::string& name) const {
    auto it = input_plugins_.find(name);
    return (it != input_plugins_.end()) ? &it->second : nullptr;
}

std::unique_ptr<APluginTransformation, TransformationPluginDestroyer> 
PluginRegistry::createTransformation(const std::string& name, 
                                     const nlohmann::json& params) {
    const auto* metadata = getTransformation(name);
    if (!metadata || !metadata->library_handle) {
        std::cerr << "Error: Transformation plugin not found: " << name << std::endl;
        return {nullptr, nullptr};
    }
    
    auto create_fn = reinterpret_cast<TransformationPluginCreator>(
        dlsym(metadata->library_handle, "create"));
    auto destroy_fn = reinterpret_cast<TransformationPluginDestroyer>(
        dlsym(metadata->library_handle, "destroy"));
    
    if (!create_fn || !destroy_fn) {
        std::cerr << "Error: Failed to get plugin factory functions" << std::endl;
        return {nullptr, nullptr};
    }
    
    return {create_fn(params), destroy_fn};
}

std::unique_ptr<APluginInput, InputPluginDestroyer> 
PluginRegistry::createInput(const std::string& name, 
                            const nlohmann::json& params) {
    const auto* metadata = getInput(name);
    if (!metadata || !metadata->library_handle) {
        std::cerr << "Error: Input plugin not found: " << name << std::endl;
        return {nullptr, nullptr};
    }
    
    auto create_fn = reinterpret_cast<InputPluginCreator>(
        dlsym(metadata->library_handle, "create"));
    auto destroy_fn = reinterpret_cast<InputPluginDestroyer>(
        dlsym(metadata->library_handle, "destroy"));
    
    if (!create_fn || !destroy_fn) {
        std::cerr << "Error: Failed to get plugin factory functions" << std::endl;
        return {nullptr, nullptr};
    }
    
    return {create_fn(params), destroy_fn};
}

std::vector<std::string> PluginRegistry::getTransformationNames() const {
    std::vector<std::string> names;
    for (const auto& [name, _] : transformation_plugins_) {
        names.push_back(name);
    }
    return names;
}

std::vector<std::string> PluginRegistry::getInputNames() const {
    std::vector<std::string> names;
    for (const auto& [name, _] : input_plugins_) {
        names.push_back(name);
    }
    return names;
}

// ============================================================================
// PluginLoader Implementation
// ============================================================================

void* PluginLoader::loadLibrary(const std::filesystem::path& library_path) {
    void* handle = dlopen(library_path.c_str(), RTLD_LAZY);
    if (!handle) {
        std::cerr << "Error loading library " << library_path << ": " 
                  << dlerror() << std::endl;
    }
    return handle;
}

void* PluginLoader::getFunction(void* handle, const std::string& function_name) {
    if (!handle) return nullptr;
    
    void* func = dlsym(handle, function_name.c_str());
    if (!func) {
        std::cerr << "Error getting function " << function_name << ": " 
                  << dlerror() << std::endl;
    }
    return func;
}

std::unique_ptr<PluginMetadata> PluginLoader::loadPlugin(
    const std::filesystem::path& plugin_dir,
    const std::string& plugin_type) {
    
    auto json_file = plugin_dir / "plugin.json";
    if (!std::filesystem::exists(json_file)) {
        std::cerr << "Warning: No plugin.json found in " << plugin_dir << std::endl;
        return nullptr;
    }
    
    // Parse JSON
    std::ifstream file(json_file);
    if (!file.is_open()) {
        std::cerr << "Error: Cannot open " << json_file << std::endl;
        return nullptr;
    }
    
    nlohmann::json json_data;
    try {
        file >> json_data;
    } catch (const nlohmann::json::exception& e) {
        std::cerr << "Error: Invalid JSON in " << json_file << ": " << e.what() << std::endl;
        return nullptr;
    }
    
    // Validate plugin type
    if (json_data["type"] != plugin_type) {
        return nullptr;
    }
    
    auto metadata = std::make_unique<PluginMetadata>();
    metadata->name = json_data["name"];
    metadata->version = json_data["version"];
    metadata->type = json_data["type"];
    metadata->description = json_data.value("description", "");
    metadata->author = json_data.value("author", "");
    metadata->cpp_library = json_data["cpp_library"];
    metadata->python_library = json_data.value("python_library", "");
    metadata->class_name = json_data["class_name"];
    metadata->parameters = json_data.value("parameters", nlohmann::json::array());
    metadata->path = plugin_dir;
    
    // Load C++ library
    auto cpp_lib_path = plugin_dir / metadata->cpp_library;
    if (!std::filesystem::exists(cpp_lib_path)) {
        std::cerr << "Warning: C++ library not found: " << cpp_lib_path << std::endl;
        return nullptr;
    }
    
    metadata->library_handle = loadLibrary(cpp_lib_path);
    if (!metadata->library_handle) {
        return nullptr;
    }
    
    std::cout << "Loaded plugin: " << metadata->name << " v" << metadata->version << std::endl;
    return metadata;
}

std::vector<PluginMetadata> PluginLoader::discoverPlugins(
    const std::filesystem::path& plugins_root,
    const std::string& plugin_type) {
    
    std::filesystem::path plugin_dir;
    if (plugin_type == "transformation") {
        plugin_dir = plugins_root / "transformations";
    } else if (plugin_type == "input") {
        plugin_dir = plugins_root / "inputs";
    } else {
        std::cerr << "Error: Invalid plugin type: " << plugin_type << std::endl;
        return {};
    }
    
    if (!std::filesystem::exists(plugin_dir)) {
        return {};
    }
    
    std::vector<PluginMetadata> plugins;
    for (const auto& entry : std::filesystem::directory_iterator(plugin_dir)) {
        if (entry.is_directory()) {
            auto metadata = loadPlugin(entry.path(), plugin_type);
            if (metadata) {
                plugins.push_back(*metadata);
            }
        }
    }
    
    return plugins;
}

int PluginLoader::loadTransformationPlugins(const std::filesystem::path& plugins_root) {
    auto plugins = discoverPlugins(plugins_root, "transformation");
    auto& registry = PluginRegistry::getInstance();
    
    for (auto& plugin : plugins) {
        registry.registerTransformation(plugin.name, plugin);
    }
    
    return plugins.size();
}

int PluginLoader::loadInputPlugins(const std::filesystem::path& plugins_root) {
    auto plugins = discoverPlugins(plugins_root, "input");
    auto& registry = PluginRegistry::getInstance();
    
    for (auto& plugin : plugins) {
        registry.registerInput(plugin.name, plugin);
    }
    
    return plugins.size();
}

std::pair<int, int> PluginLoader::loadAllPlugins(const std::filesystem::path& plugins_root) {
    int num_transformations = loadTransformationPlugins(plugins_root);
    int num_inputs = loadInputPlugins(plugins_root);
    return {num_transformations, num_inputs};
}

} // namespace vc
