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

class Rectangle final : public AInput
{
public:
    explicit Rectangle(nlohmann::json::object_t&& args)
        : AInput(std::move(args))
    {
    }

    cv::Mat getBaseMatrix(const nlohmann::json::object_t& args) override
    {
        size_t w = args.at("width");
        size_t h = args.at("height");
        size_t t = args.at("thickness");
        const std::vector<int>& color = args.at("color");
        size_t r = args.at("cornerRadius");
        bool filled = args.at("filled");
        const cv::Vec4b bgra = cv::Scalar(color[2], color[1], color[0], color[3]);
        cv::LineTypes lineType = cv::LINE_AA;

        cv::Mat mat = cv::Mat(h, w, CV_8UC4).setTo(cv::Scalar(0, 0, 0, 0));

        size_t a = r ? t / 2 : 0;

        if (r) {
            cv::ellipse(mat, cv::Point2d(r + a, r + a), cv::Size(r, r), 180, 0, 90, bgra, t, lineType);
            cv::ellipse(mat, cv::Point2d(w - r - a - 1, r + a), cv::Size(r, r), 180, 90, 180, bgra, t, lineType);
            cv::ellipse(mat, cv::Point2d(w - r - a - 1, h - r - a - 1), cv::Size(r, r), 180, 180, 270, bgra, t, lineType);
            cv::ellipse(mat, cv::Point2d(r + a, h - r - a - 1), cv::Size(r, r), 180, 270, 360, bgra, t, lineType);
        }

        fillLine(mat, r + a, 0, w - r - a, t, bgra);
        fillLine(mat, r + a, h - t, w - r - a, h, bgra);
        fillLine(mat, w - t, r + a, w, h - r - a, bgra);
        fillLine(mat, 0, r + a, t, h - r - a, bgra);

        if (filled) {
            for (size_t y = 0; y < h; y++) {
                for (size_t x = w / 2; x < w; x++) {
                    if (mat.at<cv::Vec4b>(y, x)[3] != bgra[3]) {
                        mat.at<cv::Vec4b>(y, x) = bgra;
                        continue;
                    }
                    break;
                }
                for (size_t x = w / 2 - 1; x > 0; x--) {
                    if (mat.at<cv::Vec4b>(y, x)[3] != bgra[3]) {
                        mat.at<cv::Vec4b>(y, x) = bgra;
                        continue;
                    }
                    break;
                }
            }
        }

        return mat;
    }
};

static std::unique_ptr<IInput> createRectangle(nlohmann::json::object_t&& args)
{
    return std::make_unique<Rectangle>(std::move(args));
}

extern "C" void vc_register_plugin(VC::PluginRegistrar* registrar)
{
    registrar->registerInput(registrar->context, "Rectangle", createRectangle);
}
