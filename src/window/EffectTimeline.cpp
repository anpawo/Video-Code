/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** EffectTimeline
*/

#include "window/EffectTimeline.hpp"

#include <QFileInfo>
#include <QFontMetrics>
#include <QMouseEvent>
#include <QPainter>
#include <QPaintEvent>
#include <QString>
#include <QTimer>
#include <algorithm>
#include <cmath>

namespace VC
{

namespace
{
    constexpr int kMinTotalFrames = 60;
    constexpr int kRulerMinTickPx = 56;

    QColor effectColor(const QString& kind, bool selected)
    {
        QColor base = QColor(70, 110, 200);
        if (kind == "vertex") {
            base = QColor(140, 90, 200);
        } else if (kind == "fragment") {
            base = QColor(70, 140, 180);
        }
        if (selected) {
            base = base.lighter(140);
        }
        return base;
    }

    QString inputDisplayName(const nlohmann::json& input)
    {
        QString name;
        if (input.is_object() && input.contains("name")) {
            name = QString::fromStdString(input["name"].get<std::string>());
        }
        if (!name.isEmpty()) {
            name[0] = name[0].toUpper();
        }

        if (!input.is_object() || !input.contains("params")) {
            return name;
        }
        const auto& params = input["params"];
        if (!params.is_array()) {
            return name;
        }
        for (const auto& p : params) {
            if (!p.contains("name") || p["name"] != "filepath" || !p.contains("value") ||
                !p["value"].is_string()) {
                continue;
            }
            const QString filename = QFileInfo(QString::fromStdString(p["value"].get<std::string>())).fileName();
            if (!filename.isEmpty()) {
                return name + " | " + filename;
            }
        }
        return name;
    }
}

EffectTimeline::EffectTimeline(QWidget* parent)
    : QWidget(parent)
{
    setObjectName("effectTimeline");
    setMouseTracking(true);
    setMinimumHeight(160);
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::MinimumExpanding);

    _animTimer = new QTimer(this);
    _animTimer->setInterval(16);
    QObject::connect(_animTimer, &QTimer::timeout, this, [this]() { stepAnimation(); });
}

void EffectTimeline::setProject(
    const std::vector<nlohmann::json>& inputs,
    const std::vector<std::vector<nlohmann::json>>& effectsByInput,
    size_t totalFrames,
    size_t currentFrame
)
{
    _inputs = inputs;
    _effectsByInput = effectsByInput;
    _totalFrames = std::max<size_t>(totalFrames, kMinTotalFrames);
    _currentFrame = std::min(currentFrame, _totalFrames > 0 ? _totalFrames - 1 : 0);

    if (_expanded.size() != _inputs.size()) {
        _expanded.resize(_inputs.size(), false);
    }
    if (_progress.size() != _inputs.size()) {
        _progress.resize(_inputs.size(), 0.0);
    }
    update();
}

void EffectTimeline::setSelection(int inputIndex, int effectIndex)
{
    _selectedInput = inputIndex;
    _selectedEffect = effectIndex;
    update();
}

void EffectTimeline::setCurrentFrame(size_t currentFrame)
{
    const size_t clamped = _totalFrames > 0 ? std::min(currentFrame, _totalFrames - 1) : 0;
    if (clamped == _currentFrame) {
        return;
    }
    _currentFrame = clamped;
    update();
}

int EffectTimeline::contentWidth() const
{
    return std::max(0, width() - leftLabelWidth() - rightPadding());
}

double EffectTimeline::pxPerFrame() const
{
    if (_totalFrames == 0) {
        return 0.0;
    }
    return static_cast<double>(contentWidth()) / static_cast<double>(_totalFrames);
}

int EffectTimeline::frameToX(size_t frame) const
{
    return leftLabelWidth() + static_cast<int>(std::round(frame * pxPerFrame()));
}

size_t EffectTimeline::xToFrame(int x) const
{
    const double pf = pxPerFrame();
    if (pf <= 0.0) {
        return 0;
    }
    const double relative = static_cast<double>(x - leftLabelWidth());
    const long long f = static_cast<long long>(std::round(relative / pf));
    if (f < 0) return 0;
    if (static_cast<size_t>(f) > _totalFrames) return _totalFrames;
    return static_cast<size_t>(f);
}

double EffectTimeline::easedProgress(int inputIndex) const
{
    if (inputIndex < 0 || static_cast<size_t>(inputIndex) >= _progress.size()) {
        return 0.0;
    }
    const double t = std::clamp(_progress[inputIndex], 0.0, 1.0);
    // easeInOutCubic
    return t < 0.5 ? 4.0 * t * t * t : 1.0 - std::pow(-2.0 * t + 2.0, 3.0) / 2.0;
}

double EffectTimeline::expansionHeightFor(int inputIndex) const
{
    if (inputIndex < 0 || static_cast<size_t>(inputIndex) >= _effectsByInput.size()) {
        return 0.0;
    }
    const size_t n = _effectsByInput[inputIndex].size();
    if (n == 0) {
        return 0.0;
    }
    const double full = static_cast<double>(n) * (subRowHeight() + subRowSpacing()) + subRowSpacing();
    return easedProgress(inputIndex) * full;
}

int EffectTimeline::trackTop(int inputIndex) const
{
    int y = rulerHeight() + trackSpacing();
    for (int k = 0; k < inputIndex; ++k) {
        y += trackHeight() + static_cast<int>(std::round(expansionHeightFor(k))) + trackSpacing();
    }
    return y;
}

QString EffectTimeline::trackLabel(int inputIndex) const
{
    if (inputIndex < 0 || static_cast<size_t>(inputIndex) >= _inputs.size()) {
        return QString();
    }
    return inputDisplayName(_inputs[inputIndex]);
}

void EffectTimeline::paintEvent(QPaintEvent*)
{
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing, false);

    // Background
    painter.fillRect(rect(), QColor("#111317"));

    // Ruler background
    QRect rulerRect(0, 0, width(), rulerHeight());
    painter.fillRect(rulerRect, QColor("#181b20"));
    painter.setPen(QColor("#2a3037"));
    painter.drawLine(0, rulerHeight() - 1, width(), rulerHeight() - 1);

    // Ruler ticks
    const double pf = pxPerFrame();
    if (pf > 0.0) {
        int stepFrames = 1;
        while (stepFrames * pf < kRulerMinTickPx) {
            if (stepFrames < 5) stepFrames = 5;
            else if (stepFrames < 10) stepFrames = 10;
            else if (stepFrames < 30) stepFrames = 30;
            else if (stepFrames < 60) stepFrames = 60;
            else stepFrames *= 2;
        }
        painter.setPen(QColor("#8c959f"));
        QFont font = painter.font();
        font.setPointSizeF(font.pointSizeF() * 0.92);
        painter.setFont(font);
        for (size_t f = 0; f <= _totalFrames; f += stepFrames) {
            const int x = frameToX(f);
            painter.setPen(QColor("#3a4148"));
            painter.drawLine(x, rulerHeight() - 8, x, rulerHeight() - 1);
            painter.setPen(QColor("#a9b1bb"));
            painter.drawText(x + 4, rulerHeight() - 10, QString("f%1").arg(f));
        }
    }

    // Tracks
    painter.setPen(Qt::NoPen);
    for (size_t i = 0; i < _inputs.size(); ++i) {
        const int top = trackTop(static_cast<int>(i));

        // Track row background
        QRect rowRect(0, top, width(), trackHeight());
        painter.fillRect(rowRect, (i % 2 == 0) ? QColor("#16181d") : QColor("#13151a"));

        // Input lifespan band (shows when the input is visible)
        const auto& input = _inputs[i];
        const size_t inStart = input.value("startFrame", static_cast<size_t>(0));
        const size_t inDuration = input.value("duration", static_cast<size_t>(0));
        if (inDuration > 0) {
            const int lx1 = frameToX(inStart);
            const int lx2 = frameToX(inStart + inDuration);
            QRect lifespanRect(lx1, top + 1, std::max(2, lx2 - lx1), trackHeight() - 2);
            painter.setPen(Qt::NoPen);
            painter.setBrush(QColor(60, 80, 110, 90));
            painter.drawRoundedRect(lifespanRect, 4, 4);
        }

        const double p = easedProgress(static_cast<int>(i));

        // Chevron indicator: ▶ collapsed, ▼ expanded
        const bool hasEffects = i < _effectsByInput.size() && !_effectsByInput[i].empty();
        if (hasEffects) {
            painter.setPen(QColor("#8c959f"));
            painter.save();
            const QPointF chevronCenter(16, top + trackHeight() / 2.0);
            painter.translate(chevronCenter);
            painter.rotate(p * 90.0);
            QPolygonF chevron;
            chevron << QPointF(-3, -4) << QPointF(3, 0) << QPointF(-3, 4);
            painter.setBrush(QColor("#8c959f"));
            painter.setPen(Qt::NoPen);
            painter.drawPolygon(chevron);
            painter.restore();
        }

        // Label area (offset to leave room for chevron)
        const int labelLeft = hasEffects ? 26 : 8;
        QRect labelRect(labelLeft, top, leftLabelWidth() - labelLeft - 4, trackHeight());
        painter.setPen(QColor("#cdd3d8"));
        const QString label = trackLabel(static_cast<int>(i));
        const QString elided = QFontMetrics(painter.font())
                                   .elidedText(label, Qt::ElideRight, labelRect.width());
        painter.drawText(labelRect, Qt::AlignVCenter | Qt::AlignLeft, elided);

        // Track separator line
        painter.setPen(QColor("#22262d"));
        painter.drawLine(leftLabelWidth(), top + trackHeight() - 1, width() - rightPadding(),
                         top + trackHeight() - 1);

        // Clips
        if (i >= _effectsByInput.size()) {
            continue;
        }
        const auto& effects = _effectsByInput[i];

        auto drawClip = [&](size_t e, const QRect& clipRect, double opacity) {
            const auto& eff = effects[e];
            const QString kind = QString::fromStdString(eff.value("kind", "fragment"));
            const QString name = QString::fromStdString(eff.value("name", ""));
            const bool selected = (static_cast<int>(i) == _selectedInput &&
                                   static_cast<int>(e) == _selectedEffect);
            QColor fill = effectColor(kind, selected);
            fill.setAlphaF(std::clamp(opacity, 0.0, 1.0));
            painter.setPen(Qt::NoPen);
            painter.setBrush(fill);
            painter.drawRoundedRect(clipRect, 5, 5);

            if (selected) {
                QColor outline("#ffffff");
                outline.setAlphaF(std::clamp(opacity, 0.0, 1.0));
                painter.setPen(QPen(outline, 1.4));
                painter.setBrush(Qt::NoBrush);
                painter.drawRoundedRect(clipRect.adjusted(0, 0, -1, -1), 5, 5);
            }

            QColor textColor("#ffffff");
            textColor.setAlphaF(std::clamp(opacity, 0.0, 1.0));
            painter.setPen(textColor);
            const QString elidedClip = QFontMetrics(painter.font())
                                           .elidedText(name, Qt::ElideRight,
                                                       std::max(0, clipRect.width() - 8));
            painter.drawText(clipRect.adjusted(6, 0, -6, 0), Qt::AlignVCenter | Qt::AlignLeft,
                             elidedClip);
        };

        // Collapsed view: clips drawn on the header row (fades out as we expand)
        const double headerOpacity = 1.0 - p;
        if (headerOpacity > 0.01) {
            for (size_t e = 0; e < effects.size(); ++e) {
                const auto& eff = effects[e];
                const size_t start = eff.value("startFrame", static_cast<size_t>(0));
                const size_t duration = std::max<size_t>(eff.value("duration", static_cast<size_t>(1)), 1);
                const int x1 = frameToX(start);
                const int x2 = frameToX(start + duration);
                QRect clipRect(x1, top + 4, std::max(2, x2 - x1), trackHeight() - 8);
                drawClip(e, clipRect, headerOpacity);
            }
        }

        // Expanded view: each effect on its own sub-row (fades in)
        if (p > 0.01 && !effects.empty()) {
            const int expansionTop = top + trackHeight();
            const int expansionHeight = static_cast<int>(std::round(expansionHeightFor(static_cast<int>(i))));

            painter.save();
            painter.setClipRect(0, expansionTop, width(), expansionHeight);

            // Subtle background for expansion area
            painter.fillRect(QRect(0, expansionTop, width(), expansionHeight), QColor("#0e1014"));

            for (size_t e = 0; e < effects.size(); ++e) {
                const auto& eff = effects[e];
                const size_t start = eff.value("startFrame", static_cast<size_t>(0));
                const size_t duration = std::max<size_t>(eff.value("duration", static_cast<size_t>(1)), 1);
                const int x1 = frameToX(start);
                const int x2 = frameToX(start + duration);
                const int rowY = expansionTop + subRowSpacing() +
                                 static_cast<int>(e) * (subRowHeight() + subRowSpacing());
                QRect clipRect(x1, rowY, std::max(2, x2 - x1), subRowHeight());

                // Sub-row label on the left
                QRect subLabelRect(leftLabelWidth() - 90, rowY, 86, subRowHeight());
                QColor subLabelColor("#6b7480");
                subLabelColor.setAlphaF(p);
                painter.setPen(subLabelColor);
                const QString subLabel = QString::fromStdString(eff.value("name", ""));
                const QString elidedSub = QFontMetrics(painter.font())
                                              .elidedText(subLabel, Qt::ElideRight, subLabelRect.width());
                painter.drawText(subLabelRect, Qt::AlignVCenter | Qt::AlignRight, elidedSub);

                drawClip(e, clipRect, p);
            }

            painter.restore();
        }
    }

    // Empty-state hint
    if (_inputs.empty()) {
        painter.setPen(QColor("#6b7480"));
        QFont hintFont = painter.font();
        hintFont.setItalic(true);
        painter.setFont(hintFont);
        painter.drawText(rect().adjusted(0, rulerHeight(), 0, 0),
                         Qt::AlignCenter,
                         "No inputs yet — add one from the Library");
    }

    // Playhead
    if (pf > 0.0) {
        const int x = frameToX(_currentFrame);
        painter.setPen(QPen(QColor("#e85a4f"), 1.5));
        painter.drawLine(x, 0, x, height());

        // Playhead handle on the ruler
        QRect handle(x - 6, 2, 12, rulerHeight() - 6);
        painter.setBrush(QColor("#e85a4f"));
        painter.setPen(Qt::NoPen);
        painter.drawRoundedRect(handle, 3, 3);
    }
}

bool EffectTimeline::hitTestClip(const QPoint& pos, int& outInput, int& outEffect) const
{
    if (pos.y() < rulerHeight()) {
        return false;
    }
    for (size_t i = 0; i < _inputs.size(); ++i) {
        const int top = trackTop(static_cast<int>(i));
        const int headerBottom = top + trackHeight();
        const double p = easedProgress(static_cast<int>(i));

        // Header row: clip hit-test only when not (fully) expanded
        if (pos.y() >= top && pos.y() < headerBottom && pos.x() >= leftLabelWidth() && p < 0.5) {
            if (i >= _effectsByInput.size()) {
                return false;
            }
            const auto& effects = _effectsByInput[i];
            for (size_t e = 0; e < effects.size(); ++e) {
                const auto& eff = effects[e];
                const size_t start = eff.value("startFrame", static_cast<size_t>(0));
                const size_t duration = std::max<size_t>(eff.value("duration", static_cast<size_t>(1)), 1);
                const int x1 = frameToX(start);
                const int x2 = frameToX(start + duration);
                if (pos.x() >= x1 && pos.x() <= x2) {
                    outInput = static_cast<int>(i);
                    outEffect = static_cast<int>(e);
                    return true;
                }
            }
            return false;
        }

        // Sub-rows: hit-test when expanded enough
        if (p >= 0.5 && i < _effectsByInput.size()) {
            const auto& effects = _effectsByInput[i];
            const int expansionTop = headerBottom;
            for (size_t e = 0; e < effects.size(); ++e) {
                const int rowY = expansionTop + subRowSpacing() +
                                 static_cast<int>(e) * (subRowHeight() + subRowSpacing());
                if (pos.y() < rowY || pos.y() >= rowY + subRowHeight()) {
                    continue;
                }
                const auto& eff = effects[e];
                const size_t start = eff.value("startFrame", static_cast<size_t>(0));
                const size_t duration = std::max<size_t>(eff.value("duration", static_cast<size_t>(1)), 1);
                const int x1 = frameToX(start);
                const int x2 = frameToX(start + duration);
                if (pos.x() >= x1 && pos.x() <= x2) {
                    outInput = static_cast<int>(i);
                    outEffect = static_cast<int>(e);
                    return true;
                }
            }
        }
    }
    return false;
}

int EffectTimeline::hitTestInputRow(const QPoint& pos) const
{
    if (pos.y() < rulerHeight()) {
        return -1;
    }
    for (size_t i = 0; i < _inputs.size(); ++i) {
        const int top = trackTop(static_cast<int>(i));
        if (pos.y() >= top && pos.y() < top + trackHeight()) {
            return static_cast<int>(i);
        }
    }
    return -1;
}

void EffectTimeline::toggleExpansion(int inputIndex)
{
    if (inputIndex < 0 || static_cast<size_t>(inputIndex) >= _expanded.size()) {
        return;
    }
    if (inputIndex < static_cast<int>(_effectsByInput.size()) && _effectsByInput[inputIndex].empty()) {
        return; // nothing to expand
    }
    _expanded[inputIndex] = !_expanded[inputIndex];
    if (_animTimer && !_animTimer->isActive()) {
        _animTimer->start();
    }
}

void EffectTimeline::stepAnimation()
{
    const double step = 0.12;
    bool stillAnimating = false;
    for (size_t i = 0; i < _progress.size(); ++i) {
        const double target = (i < _expanded.size() && _expanded[i]) ? 1.0 : 0.0;
        if (std::abs(_progress[i] - target) < 1e-3) {
            _progress[i] = target;
            continue;
        }
        if (target > _progress[i]) {
            _progress[i] = std::min(target, _progress[i] + step);
        } else {
            _progress[i] = std::max(target, _progress[i] - step);
        }
        stillAnimating = true;
    }
    if (!stillAnimating && _animTimer) {
        _animTimer->stop();
    }
    update();
}

void EffectTimeline::mousePressEvent(QMouseEvent* event)
{
    if (event->button() != Qt::LeftButton) {
        QWidget::mousePressEvent(event);
        return;
    }
    const QPoint pos = event->pos();

    // Click on ruler → scrub
    if (pos.y() < rulerHeight() && pos.x() >= leftLabelWidth()) {
        _scrubbing = true;
        const size_t frame = xToFrame(pos.x());
        _currentFrame = frame;
        Q_EMIT playheadScrubbed(frame);
        update();
        return;
    }

    int inputIdx = -1;
    int effectIdx = -1;
    if (hitTestClip(pos, inputIdx, effectIdx)) {
        _selectedInput = inputIdx;
        _selectedEffect = effectIdx;
        update();
        Q_EMIT clipSelected(inputIdx, effectIdx);
        return;
    }

    // Click on the input row (header, not on a clip) → toggle expansion
    const int rowIdx = hitTestInputRow(pos);
    if (rowIdx >= 0) {
        toggleExpansion(rowIdx);
    }
}

void EffectTimeline::mouseMoveEvent(QMouseEvent* event)
{
    if (_scrubbing) {
        const size_t frame = xToFrame(event->pos().x());
        _currentFrame = frame;
        Q_EMIT playheadScrubbed(frame);
        update();
        return;
    }
    QWidget::mouseMoveEvent(event);
}

void EffectTimeline::mouseReleaseEvent(QMouseEvent* event)
{
    if (event->button() == Qt::LeftButton && _scrubbing) {
        _scrubbing = false;
        return;
    }
    QWidget::mouseReleaseEvent(event);
}

QSize EffectTimeline::sizeHint() const
{
    return QSize(800, 220);
}

}
