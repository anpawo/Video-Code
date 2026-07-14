/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** UiPanel
*/

#pragma once

#include <QWidget>
#include <QString>
#include <nlohmann/json.hpp>
#include <vector>

class QLabel;
class QFormLayout;
class QListWidget;
class QPushButton;
class QResizeEvent;
class QScrollArea;
class QShortcut;
class QSpinBox;
class QSplitter;
class QTimer;
class QTreeWidget;

namespace VC
{
    class Core;
    class EffectTimeline;

    class UiPanel : public QWidget
    {
        Q_OBJECT

    public:
        UiPanel(QLabel* preview, Core* core, QWidget* parent = nullptr);
        void resizeEvent(QResizeEvent* event) override;

    private:
        QLabel* _preview{nullptr};
        QWidget* _previewPane{nullptr};
        QWidget* _previewStage{nullptr};
        QWidget* _leftPane{nullptr};
        QWidget* _rightPane{nullptr};
        QSplitter* _splitter{nullptr};
        QSplitter* _centerSplitter{nullptr};
        EffectTimeline* _timeline{nullptr};
        QSpinBox* _lifespanStartSpin{nullptr};
        QSpinBox* _lifespanDurationSpin{nullptr};
        QTimer* _playheadTimer{nullptr};
        QPushButton* _playPauseBtn{nullptr};
        QLabel* _frameCounter{nullptr};
        Core* _core{nullptr};

        QTreeWidget* _effectTree{nullptr};
        QListWidget* _inputList{nullptr};
        QListWidget* _effectStackList{nullptr};
        QPushButton* _addInputBtn{nullptr};
        QScrollArea* _inspectorScroll{nullptr};
        QWidget* _inspector{nullptr};
        QFormLayout* _inspectorForm{nullptr};
        QTimer* _uiDebounce{nullptr};
        QShortcut* _enterShortcut{nullptr};

        QString _currentKind{};
        QString _currentName{};
        nlohmann::json _currentParams{};
        nlohmann::json _schema{};
        nlohmann::json _uiInput{};
        nlohmann::json _uiEffect{};
        std::vector<nlohmann::json> _inputs{};
        int _activeInputIndex{-1};
        bool _isCreatingNewInput{false};
        std::vector<std::vector<nlohmann::json>> _effectsByInput{};
        int _activeEffectIndex{-1};

        std::vector<QWidget*> _inspectorEditors{};
        std::vector<QString> _inspectorParamNames{};
        std::vector<QString> _inspectorParamTypes{};

        nlohmann::json loadUiSchema() const;
        void buildUi();
        void populateEffectTree(const nlohmann::json& schema);
        void showInspectorFor(const QString& name, const nlohmann::json& params);
        void clearInspector();
        void updateCurrentDefinitionFromInspector();
        void scheduleUiRefresh();
        void refreshPreviewFromUi();
        static QString upperFirst(const QString& s);
        void addOrUpdateInput();
        bool buildCreateArgs(const nlohmann::json& inputDef, nlohmann::json::object_t& outArgs);
        void addOrUpdateEffect();
        void removeSelectedInput();
        void refreshEffectStackList();
        void removeSelectedEffect();
        void removeEffectAt(int index);
        void renderVideo();
        void updatePreviewSize();
        void showInspectorMessage(const QString& title, const QString& body);
        QString inputListLabel(const nlohmann::json& inputDef) const;
        QString fileDialogFilterForInput(const QString& inputName) const;
        nlohmann::json schemaParamsFor(const QString& name, const QString& kind) const;
        void refreshStudioState();
        // Stack building helpers
        bool buildStack(nlohmann::json::array_t& outStack);
        bool appendInputCreate(const nlohmann::json& inputDef, nlohmann::json::array_t& outStack);
        void appendInputLifespan(const nlohmann::json& inputDef, int inputIndex, nlohmann::json::array_t& outStack);
        void appendEffectApply(const nlohmann::json& effDef, int inputIndex, nlohmann::json::array_t& outStack);
        void fillEditorFromEffect(QWidget* editor, const nlohmann::json& effectParams, const QString& pname);
        size_t timelineFrameCount() const;
        void refreshTimelineView();
        void onTimelineClipSelected(int inputIndex, int effectIndex);
        void onTimelineScrubbed(size_t frame);
        void togglePlayPause();
        void updatePlayPauseButton();
    };
};
