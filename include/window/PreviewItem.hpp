/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** PreviewItem
*/

#pragma once

#include <QImage>
#include <QQuickItem>

namespace VC
{
    class Editor;

    // -----------------------------------------------------------------------
    // PreviewItem
    //   The rendered frame, in a Qt Quick pane.
    //
    //   It owns nothing. The engine and the Vulkan device are members of
    //   VC::Editor, because a `.qml` save destroys and rebuilds every root
    //   object and a device torn down mid-frame is a crash rather than a
    //   reload. This item asks for a picture and draws it.
    //
    //   The picture arrives as a QImage and becomes a QSGSimpleTextureNode.
    //   Not a QQuickImageProvider — that is pull-based and keyed by URL, so a
    //   moving picture would mean a cache-busting id per frame through
    //   QQuickPixmapCache. And not QQuickRhiItem: that hands you Quick's own
    //   Metal QRhi, which would mean re-expressing the whole Vulkan renderer a
    //   third time.
    //
    //   It renders at the item's PHYSICAL size, which is a fraction of the
    //   output: 4x SSAA makes a 1080p frame a 7680x4320 offscreen image, and
    //   the pane is what you are looking at.
    // -----------------------------------------------------------------------
    class PreviewItem : public QQuickItem
    {
        Q_OBJECT
        Q_PROPERTY(VC::Editor* shell READ shell WRITE setShell NOTIFY shellChanged)
        Q_PROPERTY(int frame READ frame WRITE setFrame NOTIFY frameChanged)
        Q_PROPERTY(int revision READ revision WRITE setRevision NOTIFY revisionChanged)

    public:

        explicit PreviewItem(QQuickItem* parent = nullptr);

        Editor* shell() const { return _shell; }

        void setShell(Editor* shell);

        int frame() const { return _frame; }

        void setFrame(int frame);

        // Bumped by the shell after every execute: the same frame index means a
        // different picture once the scene has changed.
        int revision() const { return _revision; }

        void setRevision(int revision);

    Q_SIGNALS:

        void shellChanged();
        void frameChanged();
        void revisionChanged();

    protected:

        QSGNode* updatePaintNode(QSGNode* old, UpdatePaintNodeData*) override;
        void     geometryChange(const QRectF& next, const QRectF& previous) override;
        void     itemChange(ItemChange change, const ItemChangeData& data) override;
        void     updatePolish() override;

    private:

        Editor* _shell = nullptr;
        int     _frame = 0;
        int     _revision = 0;

        // The last frame rendered, produced on the GUI thread and uploaded on
        // the render thread. `_fresh` is what tells the two apart.
        QImage _picture;
        bool   _fresh = false;
    };
} // namespace VC
