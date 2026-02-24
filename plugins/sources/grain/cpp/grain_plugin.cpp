#include <cmath>
#include <opencv2/opencv.hpp>

#include "plugin/PluginAPI.hpp"

class Grain final : public IFragmentShader
{
public:
    explicit Grain(const nlohmann::json::object_t& args)
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

        cv::Mat noise(mat.size(), CV_16SC1);
        cv::randn(noise, 0, static_cast<int>(amount * 64.0));

        for (int y = 0; y < mat.rows; ++y) {
            auto* row = mat.ptr<cv::Vec4b>(y);
            const short* nrow = noise.ptr<short>(y);

            for (int x = 0; x < mat.cols; ++x) {
                const int delta = nrow[x];

                row[x][0] = cv::saturate_cast<uchar>(row[x][0] + delta);
                row[x][1] = cv::saturate_cast<uchar>(row[x][1] + delta);
                row[x][2] = cv::saturate_cast<uchar>(row[x][2] + delta);
            }
        }
    }

private:
    size_t _start;
    nlohmann::json::object_t _args;
};

static std::unique_ptr<IFragmentShader> createShader(const nlohmann::json::object_t& args)
{
    return std::make_unique<Grain>(args);
}

extern "C" void vc_register_plugin(VC::PluginRegistrar* registrar)
{
    registrar->registerFragmentShader(registrar->context, "Grain", createShader);
}
