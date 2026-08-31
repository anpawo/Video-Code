/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** ThumbProvider
*/

#pragma once

#include <QImage>
#include <QQuickImageProvider>
#include <QString>

namespace VC
{
    // -----------------------------------------------------------------------
    // ThumbProvider
    //   The bin's pictures: one small, cheap frame per file.
    //
    //   Deliberately tiny and deliberately rough.  A media browser that decodes
    //   full-resolution frames to draw them at ninety pixels spends a laptop's
    //   battery on pixels nobody can see — so the decode is asked for the size
    //   it will be drawn at, the frame is the FIRST one of a video (no seeking,
    //   which on a long file is the expensive part), and nothing is kept in
    //   memory beyond the QImage Qt's own pixmap cache holds.
    //
    //   Nothing else in the chrome touches the filesystem: a panel asks for
    //   "image://thumb/<path>" and gets a picture or nothing, and "nothing" is
    //   drawn as the coloured card that was there before thumbnails existed.
    // -----------------------------------------------------------------------
    class ThumbProvider : public QQuickImageProvider
    {
    public:

        ThumbProvider();
        ~ThumbProvider() override = default;

        QImage requestImage(const QString& id, QSize* size, const QSize& requestedSize) override;

    private:

        // decodeFirstFrame() — a video's opening frame, or a null image.
        static QImage decodeFirstFrame(const QString& path, int wanted);

        // decodeStill() — an image file, scaled down on the way in.
        static QImage decodeStill(const QString& path, int wanted);
    };
} // namespace VC
