#include <cmath>
#include <opencv2/opencv.hpp>

#include "plugin/PluginAPI.hpp"

class Gamma final : public IFragmentShader
{
public:
    explicit Gamma(const nlohmann::json::object_t& args)
        : _start(args.at("start").get<size_t>())
        , _args(args)
    {
    }

    size_t start() const override
    {
        return _start;
    }

    void render(cv::Mat& mat, size_t) const override
    {
        double gamma = _args.at("gamma");

        if (gamma <= 0.0) {
            gamma = 1.0;
        }

        const double invGamma = 1.0 / gamma;

        cv::Mat lut(1, 256, CV_8UC1);
        for (int i = 0; i < 256; ++i) {
            const double normalized = i / 255.0;
            lut.at<uchar>(i) = cv::saturate_cast<uchar>(std::pow(normalized, invGamma) * 255.0);
        }

        cv::LUT(mat, lut, mat);
    }

private:
    size_t _start;
    nlohmann::json::object_t _args;
};

static std::unique_ptr<IFragmentShader> createShader(const nlohmann::json::object_t& args)
{
    return std::make_unique<Gamma>(args);
}

extern "C" void vc_register_plugin(VC::PluginRegistrar* registrar)
{
    registrar->registerFragmentShader(registrar->context, "Gamma", createShader);
}
