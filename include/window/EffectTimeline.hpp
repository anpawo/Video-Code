/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** EffectTimeline
*/

#pragma once

#include <QWidget>
#include <nlohmann/json.hpp>
#include <vector>

class QMouseEvent;
class QPaintEvent;
class QTimer;
class QWheelEvent;

namespace VC
{
    class EffectTimeline : public QWidget
    {
        Q_OBJECT

    public:
        explicit EffectTimeline(QWidget* parent = nullptr);

        void setProject(
            const std::vector<nlohmann::json>& inputs,
            const std::vector<std::vector<nlohmann::json>>& effectsByInput,
            size_t totalFrames,
            size_t currentFrame
        );

        void setSelection(int inputIndex, int effectIndex);
        void setCurrentFrame(size_t currentFrame);

    Q_SIGNALS:
        void clipSelected(int inputIndex, int effectIndex);
        void playheadScrubbed(size_t frame);

    protected:
        void paintEvent(QPaintEvent* event) override;
        void mousePressEvent(QMouseEvent* event) override;
        void mouseMoveEvent(QMouseEvent* event) override;
        void mouseReleaseEvent(QMouseEvent* event) override;
        QSize sizeHint() const override;

    private:
        std::vector<nlohmann::json> _inputs{};
        std::vector<std::vector<nlohmann::json>> _effectsByInput{};
        size_t _totalFrames{150};
        size_t _currentFrame{0};
        int _selectedInput{-1};
        int _selectedEffect{-1};
        bool _scrubbing{false};
        std::vector<bool> _expanded{};
        std::vector<double> _progress{};
        QTimer* _animTimer{nullptr};

        int rulerHeight() const { return 28; }
        int trackHeight() const { return 30; }
        int trackSpacing() const { return 6; }
        int subRowHeight() const { return 22; }
        int subRowSpacing() const { return 3; }
        int leftLabelWidth() const { return 110; }
        int rightPadding() const { return 12; }

        int contentWidth() const;
        double pxPerFrame() const;
        int frameToX(size_t frame) const;
        size_t xToFrame(int x) const;
        double easedProgress(int inputIndex) const;
        double expansionHeightFor(int inputIndex) const;
        int trackTop(int inputIndex) const;
        QString trackLabel(int inputIndex) const;
        bool hitTestClip(const QPoint& pos, int& outInput, int& outEffect) const;
        int hitTestInputRow(const QPoint& pos) const;
        void toggleExpansion(int inputIndex);
        void stepAnimation();
    };
}
