/**
 * @file PluginLoader.hpp
 * @brief Plugin loading system for Video-Code
 */

#pragma once

#include "PluginBase.hpp"
#include <filesystem>
#include <map>
#include <memory>
#include <string>
#include <vector>

namespace vc {

/**
 * @brief Metadata for a loaded plugin
 */
struct PluginMetadata {
    std::string name;
    std::string version;
    std::string type;           // "transformation" or "input"
    std::string description;
    std::string author;
    std::string python_library;
    std::string cpp_library;
    std::string class_name;
    nlohmann::json parameters;
    std::filesystem::path path;
    void* library_handle = nullptr;
};

/**
 * @brief Registry for loaded plugins
 */
class PluginRegistry {
public:
    static PluginRegistry& getInstance();
    
    /**
     * @brief Register a transformation plugin
     * @param name Plugin name
     * @param metadata Plugin metadata
     */
    void registerTransformation(const std::string& name, const PluginMetadata& metadata);
    
    /**
     * @brief Register an input plugin
     * @param name Plugin name
     * @param metadata Plugin metadata
     */
    void registerInput(const std::string& name, const PluginMetadata& metadata);
    
    /**
     * @brief Get transformation plugin metadata
     * @param name Plugin name
     * @return Plugin metadata or nullptr if not found
     */
    const PluginMetadata* getTransformation(const std::string& name) const;
    
    /**
     * @brief Get input plugin metadata
     * @param name Plugin name
     * @return Plugin metadata or nullptr if not found
     */
    const PluginMetadata* getInput(const std::string& name) const;
    
    /**
     * @brief Create a transformation plugin instance
     * @param name Plugin name
     * @param params Plugin parameters
     * @return Plugin instance or nullptr if creation failed
     */
    std::unique_ptr<APluginTransformation, TransformationPluginDestroyer> 
        createTransformation(const std::string& name, const nlohmann::json& params);
    
    /**
     * @brief Create an input plugin instance
     * @param name Plugin name
     * @param params Plugin parameters
     * @return Plugin instance or nullptr if creation failed
     */
    std::unique_ptr<APluginInput, InputPluginDestroyer> 
        createInput(const std::string& name, const nlohmann::json& params);
    
    /**
     * @brief Get all loaded transformation plugin names
     * @return Vector of plugin names
     */
    std::vector<std::string> getTransformationNames() const;
    
    /**
     * @brief Get all loaded input plugin names
     * @return Vector of plugin names
     */
    std::vector<std::string> getInputNames() const;

private:
    PluginRegistry() = default;
    
    std::map<std::string, PluginMetadata> transformation_plugins_;
    std::map<std::string, PluginMetadata> input_plugins_;
};

/**
 * @brief Plugin loader for discovering and loading plugins
 */
class PluginLoader {
public:
    /**
     * @brief Load a single plugin from directory
     * @param plugin_dir Path to plugin directory
     * @param plugin_type "transformation" or "input"
     * @return Plugin metadata or nullptr if loading failed
     */
    static std::unique_ptr<PluginMetadata> loadPlugin(
        const std::filesystem::path& plugin_dir,
        const std::string& plugin_type);
    
    /**
     * @brief Discover all plugins of a given type
     * @param plugins_root Root directory for plugins
     * @param plugin_type "transformation" or "input"
     * @return Vector of loaded plugin metadata
     */
    static std::vector<PluginMetadata> discoverPlugins(
        const std::filesystem::path& plugins_root,
        const std::string& plugin_type);
    
    /**
     * @brief Load all transformation plugins
     * @param plugins_root Root directory for plugins (defaults to ./plugins)
     * @return Number of plugins loaded
     */
    static int loadTransformationPlugins(
        const std::filesystem::path& plugins_root = "./plugins");
    
    /**
     * @brief Load all input plugins
     * @param plugins_root Root directory for plugins (defaults to ./plugins)
     * @return Number of plugins loaded
     */
    static int loadInputPlugins(
        const std::filesystem::path& plugins_root = "./plugins");
    
    /**
     * @brief Load all plugins (transformations and inputs)
     * @param plugins_root Root directory for plugins (defaults to ./plugins)
     * @return Pair of (num_transformation_plugins, num_input_plugins)
     */
    static std::pair<int, int> loadAllPlugins(
        const std::filesystem::path& plugins_root = "./plugins");

private:
    /**
     * @brief Load a dynamic library
     * @param library_path Path to library
     * @return Library handle or nullptr if failed
     */
    static void* loadLibrary(const std::filesystem::path& library_path);
    
    /**
     * @brief Get function from library
     * @param handle Library handle
     * @param function_name Function name
     * @return Function pointer or nullptr if not found
     */
    static void* getFunction(void* handle, const std::string& function_name);
};

} // namespace vc
