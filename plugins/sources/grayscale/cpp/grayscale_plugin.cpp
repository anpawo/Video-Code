#include <cmath>
#include <opencv2/opencv.hpp>

#include "plugin/PluginAPI.hpp"

class Grayscale final : public IFragmentShader
{
public:
    explicit Grayscale(const nlohmann::json::object_t& args)
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
        mat.forEach<cv::Vec4b>([](cv::Vec4b& p, const int*) {
            uchar gray = static_cast<uchar>(0.299 * p[2] + 0.587 * p[1] + 0.114 * p[0]);
            p[0] = p[1] = p[2] = gray;
        });
    }

private:
    size_t _start;
    nlohmann::json::object_t _args;
};

static std::unique_ptr<IFragmentShader> createShader(const nlohmann::json::object_t& args)
{
    return std::make_unique<Grayscale>(args);
}

extern "C" void vc_register_plugin(VC::PluginRegistrar* registrar)
{
    registrar->registerFragmentShader(registrar->context, "Grayscale", createShader);
}
