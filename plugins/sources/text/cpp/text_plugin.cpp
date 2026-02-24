#include <opencv2/imgproc.hpp>
#include <utility>
#include <vector>

#include "plugin/PluginAPI.hpp"
#include "input/AInput.hpp"

class Text final : public AInput
{
public:
    explicit Text(nlohmann::json::object_t&& args)
        : AInput(std::move(args))
    {
    }

    cv::Mat getBaseMatrix(const nlohmann::json::object_t& args) override
    {
        const std::string& text = args.at("text");
        double fontSize = args.at("fontSize");
        int fontThickness = args.at("fontThickness");
        const std::vector<int>& color = args.at("color");
        int font = cv::FONT_HERSHEY_SIMPLEX;

        int baseLine = 0;
        cv::Size size = cv::getTextSize(text, font, fontSize, fontThickness, &baseLine);

        cv::Mat mat = cv::Mat(size.height + baseLine, size.width, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0));

        cv::putText(mat, text, cv::Point(0, size.height), font, fontSize, cv::Scalar(color[0], color[1], color[2], color[3]), fontThickness, cv::LINE_AA);

        return mat;
    }
};

static std::unique_ptr<IInput> createText(nlohmann::json::object_t&& args)
{
    return std::make_unique<Text>(std::move(args));
}

extern "C" void vc_register_plugin(VC::PluginRegistrar* registrar)
{
    registrar->registerInput(registrar->context, "Text", createText);
}
