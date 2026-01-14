/**
 * @file gradient_cpp.cpp
 * @brief Gradient input plugin implementation
 */

#include "plugin/PluginBase.hpp"
#include <opencv2/opencv.hpp>
#include <string>

class GradientPlugin : public vc::APluginInput {
public:
    GradientPlugin(const std::array<uint8_t, 4>& color1,
                   const std::array<uint8_t, 4>& color2,
                   const std::string& direction)
        : color1_(color1), color2_(color2), direction_(direction) {}
    
    cv::Mat generate(int width, int height, int frameNumber) override {
        cv::Mat result(height, width, CV_8UC4);
        
        if (direction_ == "horizontal") {
            generateHorizontal(result);
        } else if (direction_ == "vertical") {
            generateVertical(result);
        } else if (direction_ == "diagonal") {
            generateDiagonal(result);
        } else {
            generateHorizontal(result);  // Default
        }
        
        return result;
    }
    
    std::string getName() const override {
        return "Gradient";
    }
    
    nlohmann::json serialize() const override {
        return {
            {"plugin_name", "Gradient"},
            {"color1", color1_},
            {"color2", color2_},
            {"direction", direction_}
        };
    }

private:
    void generateHorizontal(cv::Mat& frame) {
        for (int x = 0; x < frame.cols; x++) {
            float t = static_cast<float>(x) / frame.cols;
            cv::Vec4b color = interpolateColor(t);
            
            for (int y = 0; y < frame.rows; y++) {
                frame.at<cv::Vec4b>(y, x) = color;
            }
        }
    }
    
    void generateVertical(cv::Mat& frame) {
        for (int y = 0; y < frame.rows; y++) {
            float t = static_cast<float>(y) / frame.rows;
            cv::Vec4b color = interpolateColor(t);
            
            for (int x = 0; x < frame.cols; x++) {
                frame.at<cv::Vec4b>(y, x) = color;
            }
        }
    }
    
    void generateDiagonal(cv::Mat& frame) {
        float maxDist = std::sqrt(frame.cols * frame.cols + frame.rows * frame.rows);
        
        for (int y = 0; y < frame.rows; y++) {
            for (int x = 0; x < frame.cols; x++) {
                float dist = std::sqrt(x * x + y * y);
                float t = dist / maxDist;
                frame.at<cv::Vec4b>(y, x) = interpolateColor(t);
            }
        }
    }
    
    cv::Vec4b interpolateColor(float t) {
        return cv::Vec4b(
            static_cast<uint8_t>(color1_[0] * (1 - t) + color2_[0] * t),
            static_cast<uint8_t>(color1_[1] * (1 - t) + color2_[1] * t),
            static_cast<uint8_t>(color1_[2] * (1 - t) + color2_[2] * t),
            static_cast<uint8_t>(color1_[3] * (1 - t) + color2_[3] * t)
        );
    }
    
    std::array<uint8_t, 4> color1_;
    std::array<uint8_t, 4> color2_;
    std::string direction_;
};

// Plugin factory functions
extern "C" {
    vc::APluginInput* create(const nlohmann::json& params) {
        std::array<uint8_t, 4> color1 = {255, 0, 0, 255};
        std::array<uint8_t, 4> color2 = {0, 0, 255, 255};
        
        if (params.contains("color1")) {
            auto c1 = params["color1"];
            for (int i = 0; i < 4; i++) {
                color1[i] = c1[i];
            }
        }
        
        if (params.contains("color2")) {
            auto c2 = params["color2"];
            for (int i = 0; i < 4; i++) {
                color2[i] = c2[i];
            }
        }
        
        std::string direction = params.value("direction", "horizontal");
        
        return new GradientPlugin(color1, color2, direction);
    }
    
    void destroy(vc::APluginInput* plugin) {
        delete plugin;
    }
}
