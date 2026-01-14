/**
 * @file blur_cpp.cpp
 * @brief Blur transformation plugin implementation
 */

#include "plugin/PluginBase.hpp"
#include <opencv2/opencv.hpp>

class BlurPlugin : public vc::APluginTransformation {
public:
    BlurPlugin(int kernel_size, double sigma)
        : kernel_size_(kernel_size), sigma_(sigma) {
        // Ensure kernel size is odd
        if (kernel_size_ % 2 == 0) {
            kernel_size_++;
        }
    }
    
    cv::Mat apply(cv::Mat frame) override {
        cv::Mat result;
        cv::GaussianBlur(frame, result, 
                        cv::Size(kernel_size_, kernel_size_), 
                        sigma_);
        return result;
    }
    
    std::string getName() const override {
        return "Blur";
    }
    
    nlohmann::json serialize() const override {
        return {
            {"plugin_name", "Blur"},
            {"kernel_size", kernel_size_},
            {"sigma", sigma_}
        };
    }

private:
    int kernel_size_;
    double sigma_;
};

// Plugin factory functions
extern "C" {
    vc::APluginTransformation* create(const nlohmann::json& params) {
        int kernel_size = params.value("kernel_size", 5);
        double sigma = params.value("sigma", 0.0);
        return new BlurPlugin(kernel_size, sigma);
    }
    
    void destroy(vc::APluginTransformation* plugin) {
        delete plugin;
    }
}
