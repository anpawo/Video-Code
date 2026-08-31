/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** ThumbProvider
*/

#include "window/ThumbProvider.hpp"

#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/videoio.hpp>

namespace
{
    // Ninety-six pixels on the long edge. The cards are half that on a 2x
    // screen, and a thumbnail nobody can zoom has no reason to be sharper than
    // the screen it lands on.
    constexpr int kDefaultEdge = 96;

    QImage toQImage(const cv::Mat& bgr, int wanted)
    {
        if (bgr.empty())
            return {};

        const int    longest = std::max(bgr.cols, bgr.rows);
        const double scale = longest > 0 ? static_cast<double>(wanted) / longest : 1.0;

        cv::Mat small;
        if (scale < 1.0)
            // INTER_AREA is the cheap one for shrinking, and the only one that
            // does not turn a downscaled frame into aliased noise.
            cv::resize(bgr, small, cv::Size(), scale, scale, cv::INTER_AREA);
        else
            small = bgr;

        cv::Mat rgb;
        cv::cvtColor(small, rgb, cv::COLOR_BGR2RGB);

        // The QImage must own its pixels: `rgb` dies with this function.
        return QImage(rgb.data, rgb.cols, rgb.rows, static_cast<int>(rgb.step), QImage::Format_RGB888)
            .copy();
    }
} // namespace

VC::ThumbProvider::ThumbProvider()
    : QQuickImageProvider(QQuickImageProvider::Image)
{
}

QImage VC::ThumbProvider::decodeStill(const QString& path, int wanted)
{
    // IMREAD_REDUCED_COLOR_4 decodes at a QUARTER size, in the decoder, which is
    // most of the saving: a 6000-pixel photograph never becomes a 6000-pixel
    // buffer in the first place.
    cv::Mat image = cv::imread(path.toStdString(), cv::IMREAD_REDUCED_COLOR_4);
    if (image.empty())
        image = cv::imread(path.toStdString(), cv::IMREAD_COLOR);
    return toQImage(image, wanted);
}

QImage VC::ThumbProvider::decodeFirstFrame(const QString& path, int wanted)
{
    cv::VideoCapture capture(path.toStdString());
    if (!capture.isOpened())
        return {};

    cv::Mat frame;
    capture >> frame;
    capture.release();
    return toQImage(frame, wanted);
}

QImage VC::ThumbProvider::requestImage(const QString& id, QSize* size, const QSize& requestedSize)
{
    const int wanted = requestedSize.width() > 0
                           ? std::max(requestedSize.width(), requestedSize.height())
                           : kDefaultEdge;

    const QString lowered = id.toLower();
    const bool    moving = lowered.endsWith(".mp4") || lowered.endsWith(".mov") || lowered.endsWith(".mkv") || lowered.endsWith(".webm") || lowered.endsWith(".avi");

    QImage picture = moving ? decodeFirstFrame(id, wanted) : decodeStill(id, wanted);

    // A file the decoders cannot read is not an error worth a warning: the panel
    // draws its coloured card instead, which is what it did before.
    if (size)
        *size = picture.size();
    return picture;
}
