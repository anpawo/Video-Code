#include <opencv2/imgproc.hpp>
#include <utility>
#include <vector>

#include "plugin/PluginAPI.hpp"
#include "input/AInput.hpp"

static void fillLine(cv::Mat& bg, const size_t x, const size_t y, const size_t w, const size_t h, const cv::Vec4b& color)
{
    for (size_t iy = y; iy < h; iy++) {
        for (size_t ix = x; ix < w; ix++) {
            bg.at<cv::Vec4b>(iy, ix) = color;
        }
    }
}

class Line final : public AInput
{
public:
    explicit Line(nlohmann::json::object_t&& args)
        : AInput(std::move(args))
    {
    }

    cv::Mat getBaseMatrix(const nlohmann::json::object_t& args) override
    {
        size_t l = args.at("length");
        size_t t = args.at("thickness");
        const std::vector<int>& color = args.at("color");
        bool rounded = args.at("rounded");
        const cv::Vec4b bgra = cv::Scalar(color[2], color[1], color[0], color[3]);
        cv::LineTypes lineType = cv::LINE_AA;
        int radius = t / 2;
        int cy = radius;
        int leftCx = radius;
        int rightCx = l - radius - 1;

        cv::Mat mat = cv::Mat(t, l, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0));

        size_t a = rounded ? t / 2 : 0;

        if (rounded) {
            cv::circle(mat, {leftCx, cy}, radius, bgra, cv::FILLED, lineType);
            cv::circle(mat, {rightCx, cy}, radius, bgra, cv::FILLED, lineType);
        }

        fillLine(mat, a, 0, l - a, t, bgra);

        return mat;
    }
};

static std::unique_ptr<IInput> createLine(nlohmann::json::object_t&& args)
{
    return std::make_unique<Line>(std::move(args));
}

extern "C" void vc_register_plugin(VC::PluginRegistrar* registrar)
{
    registrar->registerInput(registrar->context, "Line", createLine);
}
