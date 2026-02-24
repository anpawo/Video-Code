#include <cmath>
#include <opencv2/opencv.hpp>

#include "plugin/PluginAPI.hpp"

class Opacity final : public IFragmentShader
{
public:
    explicit Opacity(const nlohmann::json::object_t& args)
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
        size_t opacity = _args.at("opacity");

        mat.forEach<cv::Vec4b>([opacity](cv::Vec4b& p, const int*) {
            if (p[3] != 0) {
                p[3] = opacity;
            }
        });
    }

private:
    size_t _start;
    nlohmann::json::object_t _args;
};

static std::unique_ptr<IFragmentShader> createShader(const nlohmann::json::object_t& args)
{
    return std::make_unique<Opacity>(args);
}

extern "C" void vc_register_plugin(VC::PluginRegistrar* registrar)
{
    registrar->registerFragmentShader(registrar->context, "Opacity", createShader);
}
