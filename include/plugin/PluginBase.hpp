/**
 * @file PluginBase.hpp
 * @brief Base classes for Video-Code plugins
 */

#pragma once

#include <opencv2/opencv.hpp>
#include <nlohmann/json.hpp>
#include <string>
#include <memory>

namespace vc {

/**
 * @brief Base class for transformation plugins
 * 
 * Transformation plugins apply effects to input frames.
 */
class APluginTransformation {
public:
    virtual ~APluginTransformation() = default;
    
    /**
     * @brief Apply the transformation to a frame
     * @param frame Input frame
     * @return Transformed frame
     */
    virtual cv::Mat apply(cv::Mat frame) = 0;
    
    /**
     * @brief Get plugin name
     * @return Plugin name
     */
    virtual std::string getName() const = 0;
    
    /**
     * @brief Serialize plugin parameters
     * @return JSON object with parameters
     */
    virtual nlohmann::json serialize() const = 0;
};

/**
 * @brief Base class for input plugins
 * 
 * Input plugins generate frames (shapes, patterns, etc.).
 */
class APluginInput {
public:
    virtual ~APluginInput() = default;
    
    /**
     * @brief Generate a frame
     * @param width Frame width
     * @param height Frame height
     * @param frameNumber Current frame number
     * @return Generated frame
     */
    virtual cv::Mat generate(int width, int height, int frameNumber) = 0;
    
    /**
     * @brief Get plugin name
     * @return Plugin name
     */
    virtual std::string getName() const = 0;
    
    /**
     * @brief Serialize plugin parameters
     * @return JSON object with parameters
     */
    virtual nlohmann::json serialize() const = 0;
};

// Plugin factory function types
using TransformationPluginCreator = APluginTransformation* (*)(const nlohmann::json&);
using TransformationPluginDestroyer = void (*)(APluginTransformation*);
using InputPluginCreator = APluginInput* (*)(const nlohmann::json&);
using InputPluginDestroyer = void (*)(APluginInput*);

} // namespace vc
