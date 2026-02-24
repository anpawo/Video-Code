#include <opencv2/imgproc.hpp>
#include <utility>
#include <vector>

#include "plugin/PluginAPI.hpp"
#include "input/AInput.hpp"

class Circle final : public AInput
{
public:
    explicit Circle(nlohmann::json::object_t&& args)
        : AInput(std::move(args))
    {
    }

    cv::Mat getBaseMatrix(const nlohmann::json::object_t& args) override
    {
        int radius = args.at("radius");
        int thickness = args.at("thickness");
        const std::vector<int>& color = args.at("color");
        bool filled = args.at("filled");

        if (thickness == 0) {
            thickness = 1;
        }

        cv::Mat mat = cv::Mat(radius * 2, radius * 2, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0));

        cv::circle(mat, cv::Point(radius, radius), radius - thickness / 2 * !filled, cv::Scalar(color[2], color[1], color[0], color[3]), filled ? cv::FILLED : thickness, cv::LINE_AA);

        return mat;
    }
};

static std::unique_ptr<IInput> createCircle(nlohmann::json::object_t&& args)
{
    return std::make_unique<Circle>(std::move(args));
}

extern "C" void vc_register_plugin(VC::PluginRegistrar* registrar)
{
    registrar->registerInput(registrar->context, "Circle", createCircle);
}
