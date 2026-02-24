#include <cmath>
#include <opencv2/opencv.hpp>

#include "plugin/PluginAPI.hpp"

class Contrast final : public IFragmentShader
{
public:
    explicit Contrast(const nlohmann::json::object_t& args)
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
        int amount = static_cast<int>(_args.at("amount"));

        if (amount == 0) {
            return;
        }

        if (amount < -255) {
            amount = -255;
        }
        if (amount > 255) {
            amount = 255;
        }

        const double alpha = (259.0 * (amount + 255.0)) / (255.0 * (259.0 - amount));
        const double beta = 128.0 * (1.0 - alpha);

        mat.convertTo(mat, -1, alpha, beta);
    }

private:
    size_t _start;
    nlohmann::json::object_t _args;
};

static std::unique_ptr<IFragmentShader> createShader(const nlohmann::json::object_t& args)
{
    return std::make_unique<Contrast>(args);
}

extern "C" void vc_register_plugin(VC::PluginRegistrar* registrar)
{
    registrar->registerFragmentShader(registrar->context, "Contrast", createShader);
}
