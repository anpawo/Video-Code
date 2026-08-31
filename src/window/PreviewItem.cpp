/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** PreviewItem
*/

#include "window/PreviewItem.hpp"

#include <QQuickWindow>
#include <QSGSimpleTextureNode>
#include <QSGTexture>

#include "window/Editor.hpp"

VC::PreviewItem::PreviewItem(QQuickItem* parent)
    : QQuickItem(parent)
{
    setFlag(ItemHasContents, true);
}

void VC::PreviewItem::setShell(Editor* shell)
{
    if (_shell == shell)
        return;
    _shell = shell;
    Q_EMIT shellChanged();
    polish();
}

void VC::PreviewItem::setFrame(int frame)
{
    if (_frame == frame)
        return;
    _frame = frame;
    Q_EMIT frameChanged();
    polish();
}

void VC::PreviewItem::setRevision(int revision)
{
    if (_revision == revision)
        return;
    _revision = revision;
    Q_EMIT revisionChanged();
    polish();
}

void VC::PreviewItem::geometryChange(const QRectF& next, const QRectF& previous)
{
    QQuickItem::geometryChange(next, previous);
    if (next.size() != previous.size())
        polish();
}

void VC::PreviewItem::itemChange(ItemChange change, const ItemChangeData& data)
{
    QQuickItem::itemChange(change, data);
    // Nothing has been drawn before the item has a window, so the first frame is
    // asked for here rather than at construction.
    if (change == ItemSceneChange && data.window != nullptr)
        polish();
}

// -----------------------------------------------------------------------
// Rendering happens HERE, on the GUI thread.
//
// `updatePaintNode` runs on the render thread, and a frame costs a Vulkan
// submit plus a walk of `Core`'s scene — which holds live `py::dict`s, and
// this codebase has never touched the GIL. Producing the picture on the
// render thread would be calling into Python from a thread Python does not
// know about. So: polish (GUI thread) produces the QImage, and
// updatePaintNode only uploads what is already there.
// -----------------------------------------------------------------------
void VC::PreviewItem::updatePolish()
{
    if (!_shell || !window() || width() <= 0 || height() <= 0)
        return;

    // Physical pixels: the item's size is in the window's logical units, and a
    // picture rendered at those is half the resolution of the screen it lands on.
    const qreal ratio = window()->effectiveDevicePixelRatio();
    const int   wide = static_cast<int>(width() * ratio);
    const int   tall = static_cast<int>(height() * ratio);

    QImage next = _shell->renderFrame(_frame, wide, tall);
    if (next.isNull())
        return;

    _picture = std::move(next);
    _fresh = true;
    update();
}

QSGNode* VC::PreviewItem::updatePaintNode(QSGNode* old, UpdatePaintNodeData*)
{
    auto* node = static_cast<QSGSimpleTextureNode*>(old);

    if (_picture.isNull()) {
        delete node;
        return nullptr;
    }

    if (!node) {
        node = new QSGSimpleTextureNode;
        node->setOwnsTexture(true);
        node->setFiltering(QSGTexture::Linear);
    }

    // Only on a new picture: a resize or a re-show repaints the node without a
    // new frame behind it, and re-uploading the same image every time would pay
    // for a texture nobody asked for.
    if (_fresh || node->texture() == nullptr) {
        node->setTexture(window()->createTextureFromImage(_picture, QQuickWindow::TextureIsOpaque));
        _fresh = false;
    }
    node->setRect(boundingRect());
    return node;
}
