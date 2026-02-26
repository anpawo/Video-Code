/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** UiPanel
*/

#pragma once

#include <QFormLayout>
#include <QListWidget>
#include <QPushButton>
#include <QShortcut>
#include <QScrollArea>
#include <QTimer>
#include <QTreeWidget>
#include <QWidget>
#include <nlohmann/json.hpp>

#include "core/Core.hpp"

namespace VC
{
    class UiPanel : public QWidget
    {
        Q_OBJECT

    public:
        UiPanel(QLabel* preview, Core* core, QWidget* parent = nullptr);

    private:
        QLabel* _preview{nullptr};
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
        nlohmann::json _uiInput{};
        nlohmann::json _uiEffect{};
        std::vector<nlohmann::json> _inputs{};
        int _activeInputIndex{-1};
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
        void refreshEffectStackList();
        void removeSelectedEffect();
        void removeEffectAt(int index);
        void renderVideo();
        // Stack building helpers
        bool buildStack(nlohmann::json::array_t& outStack);
        bool appendInputCreate(const nlohmann::json& inputDef, int index, nlohmann::json::array_t& outStack);
        void appendEffectApply(const nlohmann::json& effDef, int inputIndex, nlohmann::json::array_t& outStack);
        void fillEditorFromEffect(QWidget* editor, const nlohmann::json& effectParams, const QString& pname);
    };
};
