#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>
#include <utility>

#include "opencv2/imgproc.hpp"
#include "plugin/PluginAPI.hpp"
#include "input/AInput.hpp"
#include "utils/Exception.hpp"

class Image final : public AInput
{
public:
    explicit Image(nlohmann::json::object_t&& args)
        : AInput(std::move(args))
    {
    }

    cv::Mat getBaseMatrix(const nlohmann::json::object_t& args) override
    {
        std::string filepath = args.at("filepath");

        cv::Mat mat = cv::imread(filepath);

        if (mat.empty()) {
            throw Error("Could not load Image: " + filepath);
        }

        if (mat.channels() != 4) {
            cv::cvtColor(mat, mat, cv::COLOR_BGR2BGRA);
        }

        return mat;
    }
};

static std::unique_ptr<IInput> createImage(nlohmann::json::object_t&& args)
{
    return std::make_unique<Image>(std::move(args));
}

extern "C" void vc_register_plugin(VC::PluginRegistrar* registrar)
{
    registrar->registerInput(registrar->context, "Image", createImage);
}
