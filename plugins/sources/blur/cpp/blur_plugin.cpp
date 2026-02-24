#include <cmath>
#include <opencv2/opencv.hpp>

#include "plugin/PluginAPI.hpp"

class Blur final : public IFragmentShader
{
public:
    explicit Blur(const nlohmann::json::object_t& args)
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
        size_t strength = _args.at("strength");

        if (strength < 1) {
            strength = 1;
        }
        if (strength % 2 == 0) {
            strength++;
        }

        cv::GaussianBlur(mat, mat, cv::Size(strength, strength), 0);
    }

private:
    size_t _start;
    nlohmann::json::object_t _args;
};

static std::unique_ptr<IFragmentShader> createShader(const nlohmann::json::object_t& args)
{
    return std::make_unique<Blur>(args);
}

extern "C" void vc_register_plugin(VC::PluginRegistrar* registrar)
{
    registrar->registerFragmentShader(registrar->context, "Blur", createShader);
}
