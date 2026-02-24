#include <cmath>
#include <opencv2/opencv.hpp>

#include "plugin/PluginAPI.hpp"

class Sharpen final : public IFragmentShader
{
public:
    explicit Sharpen(const nlohmann::json::object_t& args)
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
        double amount = _args.at("amount");

        if (amount <= 0.0) {
            return;
        }
        if (amount > 1.0) {
            amount = 1.0;
        }

        cv::Mat original = mat.clone();
        cv::Mat sharpened;
        const cv::Mat kernel = (cv::Mat_<float>(3, 3) << 0, -1, 0, -1, 5, -1, 0, -1, 0);

        cv::filter2D(original, sharpened, original.depth(), kernel);
        cv::addWeighted(original, 1.0 - amount, sharpened, amount, 0.0, mat);
    }

private:
    size_t _start;
    nlohmann::json::object_t _args;
};

static std::unique_ptr<IFragmentShader> createShader(const nlohmann::json::object_t& args)
{
    return std::make_unique<Sharpen>(args);
}

extern "C" void vc_register_plugin(VC::PluginRegistrar* registrar)
{
    registrar->registerFragmentShader(registrar->context, "Sharpen", createShader);
}
