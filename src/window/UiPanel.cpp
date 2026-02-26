/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** UiPanel
*/

#include "window/UiPanel.hpp"

#include <QCheckBox>
#include <QDoubleSpinBox>
#include <QFileDialog>
#include <QFileInfo>
#include <QHBoxLayout>
#include <QLabel>
#include <QListWidget>
#include <QLineEdit>
#include <QPushButton>
#include <QShortcut>
#include <QSizePolicy>
#include <QSpinBox>
#include <QSplitter>
#include <QVBoxLayout>
#include <unordered_set>
#include <vector>
#include <string>
#include "utils/Debug.hpp"

namespace VC
{

static constexpr double WORLD_TO_SCREEN_RATIO = 120.0;

static QWidget* createEditor(const QString& type, const QString& defaultValue)
{
    const QString t = type.toLower();
    if (t.contains("bool")) {
        auto* box = new QCheckBox();
        if (defaultValue == "True" || defaultValue == "true") {
            box->setChecked(true);
        }
        return box;
    }

    if (t.contains("int") && !t.contains("float")) {
        auto* spin = new QSpinBox();
        spin->setRange(-100000, 100000);
        bool ok = false;
        const int v = defaultValue.toInt(&ok);
        if (ok) {
            spin->setValue(v);
        }
        return spin;
    }

    if (t.contains("float") || t.contains("number")) {
        auto* spin = new QDoubleSpinBox();
        spin->setDecimals(3);
        spin->setRange(-100000.0, 100000.0);
        bool ok = false;
        const double v = defaultValue.toDouble(&ok);
        if (ok) {
            spin->setValue(v);
        }
        return spin;
    }

    auto* edit = new QLineEdit();
    if (!defaultValue.isEmpty()) {
        edit->setText(defaultValue);
    }
    return edit;
}

UiPanel::UiPanel(QLabel* preview, Core* core, QWidget* parent)
    : QWidget(parent)
    , _preview(preview)
    , _core(core)
{
    _enterShortcut = new QShortcut(QKeySequence(Qt::Key_Return), this);
    connect(_enterShortcut, &QShortcut::activated, this, [this]() {
        if (_currentKind == "input") {
            addOrUpdateInput();
        } else if (_currentKind == "vertex" || _currentKind == "fragment") {
            addOrUpdateEffect();
        }
    });
    buildUi();
}

nlohmann::json UiPanel::loadUiSchema() const
{
    const std::string command = "python3 videocode/ui_schema.py --json";
    FILE* pipe = popen(command.c_str(), "r");
    if (!pipe) {
        return nlohmann::json::object();
    }

    char buffer[4096];
    std::string result;
    while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
        result += buffer;
    }
    pclose(pipe);

    try {
        return nlohmann::json::parse(result);
    } catch (...) {
        return nlohmann::json::object();
    }
}

void UiPanel::buildUi()
{
    auto* rootLayout = new QHBoxLayout(this);
    rootLayout->setContentsMargins(8, 8, 8, 8);
    rootLayout->setSpacing(8);

    _effectTree = new QTreeWidget(this);
    _effectTree->setHeaderHidden(true);
    _effectTree->setMinimumWidth(240);
    _effectTree->setStyleSheet("QTreeWidget { background: #2b2b2b; color: #e6e6e6; border: 1px solid #3a3a3a; }");

    auto* leftPane = new QWidget(this);
    auto* leftLayout = new QVBoxLayout(leftPane);
    leftLayout->setContentsMargins(0, 0, 0, 0);
    leftLayout->setSpacing(8);

    auto* renderBtn = new QPushButton("Render", leftPane);
    connect(renderBtn, &QPushButton::clicked, this, &UiPanel::renderVideo);
    leftLayout->addWidget(renderBtn);

    auto* inputLabel = new QLabel("Inputs", leftPane);
    inputLabel->setStyleSheet("color: #e6e6e6;");
    _inputList = new QListWidget(leftPane);
    _inputList->setMinimumHeight(120);
    _inputList->setStyleSheet("QListWidget { background: #2b2b2b; color: #e6e6e6; border: 1px solid #3a3a3a; }");

    leftLayout->addWidget(inputLabel);
    leftLayout->addWidget(_inputList);
    leftLayout->addWidget(_effectTree, 1);

    _inspector = new QWidget(this);
    _inspectorForm = new QFormLayout(_inspector);
    _inspectorForm->setContentsMargins(8, 8, 8, 8);
    _inspectorForm->setSpacing(8);

    _inspectorScroll = new QScrollArea(this);
    _inspectorScroll->setWidgetResizable(true);
    _inspectorScroll->setWidget(_inspector);
    _inspectorScroll->setMinimumWidth(280);
    _inspectorScroll->setStyleSheet("QScrollArea { background: #2b2b2b; border: 1px solid #3a3a3a; } QWidget { color: #e6e6e6; }");

    auto* rightPane = new QWidget(this);
    auto* rightLayout = new QVBoxLayout(rightPane);
    rightLayout->setContentsMargins(0, 0, 0, 0);
    rightLayout->setSpacing(8);

    auto* effectLabel = new QLabel("Effect Stack", rightPane);
    effectLabel->setStyleSheet("color: #e6e6e6;");
    _effectStackList = new QListWidget(rightPane);
    _effectStackList->setMinimumHeight(120);
    _effectStackList->setStyleSheet("QListWidget { background: #2b2b2b; color: #e6e6e6; border: 1px solid #3a3a3a; }");

    rightLayout->addWidget(effectLabel);
    rightLayout->addWidget(_effectStackList);

    auto* removeEffectBtn = new QPushButton("Remove Effect", rightPane);
    connect(removeEffectBtn, &QPushButton::clicked, this, &UiPanel::removeSelectedEffect);
    rightLayout->addWidget(removeEffectBtn);

    rightLayout->addWidget(_inspectorScroll, 1);

    auto* previewPane = new QWidget(this);
    auto* previewLayout = new QVBoxLayout(previewPane);
    previewLayout->setContentsMargins(8, 8, 8, 8);
    previewLayout->setAlignment(Qt::AlignCenter);
    previewLayout->addWidget(_preview);
    previewPane->setStyleSheet("background: black; border: 1px solid #3a3a3a;");

    auto* splitter = new QSplitter(Qt::Horizontal, this);
    splitter->addWidget(leftPane);
    splitter->addWidget(previewPane);
    splitter->addWidget(rightPane);
    splitter->setStretchFactor(0, 0);
    splitter->setStretchFactor(1, 1);
    splitter->setStretchFactor(2, 0);

    rootLayout->addWidget(splitter);
    setStyleSheet("background: #333333;");

    _uiDebounce = new QTimer(this);
    _uiDebounce->setSingleShot(true);
    connect(_uiDebounce, &QTimer::timeout, this, &UiPanel::refreshPreviewFromUi);

    const auto schema = loadUiSchema();
    populateEffectTree(schema);

    connect(
        _effectTree,
        &QTreeWidget::itemClicked,
        this,
        [this](QTreeWidgetItem* item, int) {
            if (!item->parent()) {
                item->setExpanded(!item->isExpanded());
                return;
            }
            const QString name = item->text(0);
            const auto paramsJson = item->data(0, Qt::UserRole).toString();
            const QString kind = item->data(0, Qt::UserRole + 1).toString();
            try {
                const auto params = nlohmann::json::parse(paramsJson.toStdString());
                _currentKind = kind;
                _currentName = name;
                _currentParams = params;
                _activeEffectIndex = -1;
                if ((_currentKind == "vertex" || _currentKind == "fragment") &&
                    _activeInputIndex >= 0 &&
                    _activeInputIndex < static_cast<int>(_effectsByInput.size())) {
                    for (size_t i = 0; i < _effectsByInput[_activeInputIndex].size(); ++i) {
                        const auto& eff = _effectsByInput[_activeInputIndex][i];
                        if (QString::fromStdString(eff.value("name", "")) == _currentName &&
                            QString::fromStdString(eff.value("kind", "")) == _currentKind) {
                            _uiEffect = eff;
                            _activeEffectIndex = static_cast<int>(i);
                            break;
                        }
                    }
                }
                showInspectorFor(name, params);
            } catch (...) {
                clearInspector();
            }
        }
    );

    connect(_inputList, &QListWidget::currentRowChanged, this, [this](int row) {
        _activeInputIndex = row;
        _activeEffectIndex = -1;
        refreshEffectStackList();
        scheduleUiRefresh();
    });

    connect(_effectStackList, &QListWidget::currentRowChanged, this, [this](int row) {
        _activeEffectIndex = row;
        if (_activeInputIndex < 0 || _activeInputIndex >= static_cast<int>(_effectsByInput.size())) {
            return;
        }
        if (row < 0 || row >= static_cast<int>(_effectsByInput[_activeInputIndex].size())) {
            return;
        }
        _uiEffect = _effectsByInput[_activeInputIndex][row];
        _currentKind = QString::fromStdString(_uiEffect.value("kind", ""));
        _currentName = QString::fromStdString(_uiEffect.value("name", ""));
        _currentParams = _uiEffect.value("params", nlohmann::json::array());
        showInspectorFor(_currentName, _currentParams);
    });
}

void UiPanel::populateEffectTree(const nlohmann::json& schema)
{
    if (!_effectTree) {
        return;
    }

    auto addCategory = [this](const QString& title) {
        auto* item = new QTreeWidgetItem(_effectTree);
        item->setText(0, title);
        item->setExpanded(false);
        return item;
    };

    auto addEntries = [](QTreeWidgetItem* category, const nlohmann::json& entries, const QString& kind) {
        if (!category || !entries.is_array()) {
            return;
        }
        for (const auto& e : entries) {
            if (!e.contains("name")) {
                continue;
            }
            auto* child = new QTreeWidgetItem(category);
            child->setText(0, QString::fromStdString(e["name"].get<std::string>()));
            if (e.contains("params")) {
                child->setData(0, Qt::UserRole, QString::fromStdString(e["params"].dump()));
            }
            child->setData(0, Qt::UserRole + 1, kind);
        }
    };

    addEntries(addCategory("Inputs"), schema.value("inputs", nlohmann::json::array()), "input");
    if (schema.contains("shaders")) {
        const auto shaders = schema["shaders"];
        addEntries(addCategory("Shaders: Vertex"), shaders.value("vertex", nlohmann::json::array()), "vertex");
        addEntries(addCategory("Shaders: Fragment"), shaders.value("fragment", nlohmann::json::array()), "fragment");
    }
    addEntries(addCategory("Templates"), schema.value("templates", nlohmann::json::array()), "template");
    addEntries(addCategory("Input Helpers"), schema.value("helpers", nlohmann::json::array()), "helper");
}

void UiPanel::clearInspector()
{
    if (!_inspectorForm) {
        return;
    }
    while (_inspectorForm->rowCount() > 0) {
        _inspectorForm->removeRow(0);
    }
    _inspectorEditors.clear();
    _inspectorParamNames.clear();
    _inspectorParamTypes.clear();
}

void UiPanel::showInspectorFor(const QString& name, const nlohmann::json& params)
{
    // Build a dynamic inspector (labels + editors) for the selected item.
    clearInspector();
    if (!_inspectorForm) {
        return;
    }

    auto* title = new QLabel(name);
    QFont f = title->font();
    f.setBold(true);
    f.setPointSize(f.pointSize() + 2);
    title->setFont(f);
    _inspectorForm->addRow(title);

    if (!params.is_array()) {
        return;
    }

    if (_currentKind == "template" || _currentKind == "helper") {
        auto* note = new QLabel("Not supported in live preview yet.");
        _inspectorForm->addRow(note);
        return;
    }

    for (const auto& p : params) {
        const QString pname = QString::fromStdString(p.value("name", ""));
        const QString ptype = QString::fromStdString(p.value("type", "Any"));
        QString pdefault;
        if (p.contains("default") && !p["default"].is_null()) {
            pdefault = QString::fromStdString(p["default"].get<std::string>());
        }

        QWidget* editor = nullptr;
        if (pname == "filepath") {
            auto* row = new QWidget(this);
            auto* rowLayout = new QHBoxLayout(row);
            rowLayout->setContentsMargins(0, 0, 0, 0);
            rowLayout->setSpacing(6);

            auto* line = new QLineEdit(row);
            if (!pdefault.isEmpty()) {
                line->setText(pdefault);
            }
            auto* browse = new QPushButton("Browse...", row);
            rowLayout->addWidget(line, 1);
            rowLayout->addWidget(browse);

            connect(browse, &QPushButton::clicked, this, [this, line]() {
                const QString path = QFileDialog::getOpenFileName(this, "Select Image", ".", "Images (*.png *.jpg *.jpeg *.gif *.bmp)");
                if (!path.isEmpty()) {
                    line->setText(path);
                }
            });

            editor = line;
            _inspectorForm->addRow(pname, row);
        } else {
            editor = createEditor(ptype, pdefault);
            _inspectorForm->addRow(pname, editor);
        }

        _inspectorEditors.push_back(editor);
        _inspectorParamNames.push_back(pname);
        _inspectorParamTypes.push_back(ptype);

        // If we are editing an existing stack entry, pre-fill with stored values.
        if (_activeEffectIndex >= 0 && _uiEffect.is_object()) {
            // When editing an existing effect, restore its stored values.
            fillEditorFromEffect(editor, _uiEffect.value("params", nlohmann::json::array()), pname);
        }


        if (auto* spin = qobject_cast<QSpinBox*>(editor)) {
            connect(spin, qOverload<int>(&QSpinBox::valueChanged), this, &UiPanel::scheduleUiRefresh);
        } else if (auto* dspin = qobject_cast<QDoubleSpinBox*>(editor)) {
            connect(dspin, qOverload<double>(&QDoubleSpinBox::valueChanged), this, &UiPanel::scheduleUiRefresh);
        } else if (auto* box = qobject_cast<QCheckBox*>(editor)) {
            connect(box, &QCheckBox::toggled, this, &UiPanel::scheduleUiRefresh);
        } else if (auto* edit = qobject_cast<QLineEdit*>(editor)) {
            // Enter is handled globally by the shortcut to avoid double-apply.
        }
    }

    if (_currentKind == "input") {
        _addInputBtn = new QPushButton("Add/Update Input");
        connect(_addInputBtn, &QPushButton::clicked, this, &UiPanel::addOrUpdateInput);
        _inspectorForm->addRow(_addInputBtn);
    } else if (_currentKind == "vertex" || _currentKind == "fragment") {
        auto* applyBtn = new QPushButton("Add/Update Effect");
        connect(applyBtn, &QPushButton::clicked, this, &UiPanel::addOrUpdateEffect);
        _inspectorForm->addRow(applyBtn);
    }

    scheduleUiRefresh();
}

void UiPanel::updateCurrentDefinitionFromInspector()
{
    VC_LOG_DEBUG("[UI] Update definition from inspector");
    nlohmann::json params = nlohmann::json::array();

    for (size_t i = 0; i < _inspectorEditors.size(); ++i) {
        const QString name = _inspectorParamNames[i];
        const QString type = _inspectorParamTypes[i].toLower();
        QWidget* editor = _inspectorEditors[i];

        nlohmann::json value = nullptr;
        if (auto* spin = qobject_cast<QSpinBox*>(editor)) {
            value = spin->value();
        } else if (auto* dspin = qobject_cast<QDoubleSpinBox*>(editor)) {
            value = dspin->value();
        } else if (auto* box = qobject_cast<QCheckBox*>(editor)) {
            value = box->isChecked();
        } else if (auto* edit = qobject_cast<QLineEdit*>(editor)) {
            const QString text = edit->text();
            if (text.isEmpty() && type.contains("maybe")) {
                value = nullptr;
            } else {
                value = text.toStdString();
            }
        }

        params.push_back(
            {
                {"name", name.toStdString()},
                {"type", type.toStdString()},
                {"value", value},
            }
        );
    }

    if (_currentKind == "input") {
        _uiInput = {
            {"name", _currentName.toStdString()},
            {"params", params},
        };
    } else if (_currentKind == "vertex" || _currentKind == "fragment") {
        _uiEffect = {
            {"name", _currentName.toStdString()},
            {"kind", _currentKind.toStdString()},
            {"params", params},
        };
    }
}

void UiPanel::scheduleUiRefresh()
{
    updateCurrentDefinitionFromInspector();
    if (_uiDebounce) {
        _uiDebounce->start(120);
    }
}

QString UiPanel::upperFirst(const QString& s)
{
    if (s.isEmpty()) {
        return s;
    }
    QString out = s;
    out[0] = out[0].toUpper();
    return out;
}

void UiPanel::refreshPreviewFromUi()
{
    // Rebuild a full stack (Create + Apply) from current UI state.
    VC_LOG_DEBUG("[UI] Refresh preview");
    updateCurrentDefinitionFromInspector();
    if (_inputs.empty()) {
        VC_LOG_DEBUG("[UI] No inputs to render");
        return;
    }

    if (_activeInputIndex < 0 || _activeInputIndex >= static_cast<int>(_inputs.size())) {
        _activeInputIndex = 0;
    }

    nlohmann::json::array_t stack;
    if (!buildStack(stack)) {
        return;
    }

    _core->loadStack(stack);
    VC_LOG_DEBUG("[UI] Stack loaded (Create+Apply)");
}

void UiPanel::addOrUpdateInput()
{
    updateCurrentDefinitionFromInspector();
    if (!_uiInput.is_object()) {
        VC_LOG_DEBUG("[UI] Add input: no input selected.");
        return;
    }

    const QString inputName = QString::fromStdString(_uiInput.value("name", ""));
    if (inputName.isEmpty()) {
        return;
    }

    if (_activeInputIndex >= 0 && _activeInputIndex < static_cast<int>(_inputs.size())) {
        _inputs[_activeInputIndex] = _uiInput;
        _inputList->item(_activeInputIndex)->setText(inputName);
    } else {
        _inputs.push_back(_uiInput);
        _effectsByInput.emplace_back();
        _inputList->addItem(inputName);
        _activeInputIndex = static_cast<int>(_inputs.size()) - 1;
        _inputList->setCurrentRow(_activeInputIndex);
    }

    refreshPreviewFromUi();
}

void UiPanel::addOrUpdateEffect()
{
    updateCurrentDefinitionFromInspector();
    if (!_uiEffect.is_object()) {
        VC_LOG_DEBUG("[UI] Add effect: no effect selected.");
        return;
    }
    if (_activeInputIndex < 0 || _activeInputIndex >= static_cast<int>(_inputs.size())) {
        VC_LOG_DEBUG("[UI] Add effect: no active input.");
        return;
    }

    if (_effectsByInput.size() < _inputs.size()) {
        _effectsByInput.resize(_inputs.size());
    }

    const QString name = QString::fromStdString(_uiEffect.value("name", ""));
    const QString kind = QString::fromStdString(_uiEffect.value("kind", ""));

    // If a specific effect is selected, update it.
    if (_activeEffectIndex >= 0 && _activeEffectIndex < static_cast<int>(_effectsByInput[_activeInputIndex].size())) {
        _effectsByInput[_activeInputIndex][_activeEffectIndex] = _uiEffect;
    } else {
        // Otherwise, ensure only one effect per name+kind.
        int existingIndex = -1;
        for (size_t i = 0; i < _effectsByInput[_activeInputIndex].size(); ++i) {
            const auto& eff = _effectsByInput[_activeInputIndex][i];
            if (QString::fromStdString(eff.value("name", "")) == name &&
                QString::fromStdString(eff.value("kind", "")) == kind) {
                existingIndex = static_cast<int>(i);
                break;
            }
        }
        if (existingIndex >= 0) {
            _effectsByInput[_activeInputIndex][existingIndex] = _uiEffect;
            _activeEffectIndex = existingIndex;
        } else {
            _effectsByInput[_activeInputIndex].push_back(_uiEffect);
            _activeEffectIndex = static_cast<int>(_effectsByInput[_activeInputIndex].size()) - 1;
        }
        _effectStackList->setCurrentRow(_activeEffectIndex);
    }

    refreshEffectStackList();
    refreshPreviewFromUi();
}

void UiPanel::refreshEffectStackList()
{
    if (!_effectStackList) {
        return;
    }
    _effectStackList->clear();
    if (_activeInputIndex < 0 || _activeInputIndex >= static_cast<int>(_effectsByInput.size())) {
        return;
    }
    for (size_t i = 0; i < _effectsByInput[_activeInputIndex].size(); ++i) {
        const auto& eff = _effectsByInput[_activeInputIndex][i];
        const QString name = QString::fromStdString(eff.value("name", ""));
        const QString kind = QString::fromStdString(eff.value("kind", ""));

        auto* item = new QListWidgetItem(_effectStackList);
        item->setSizeHint(QSize(0, 28));

        auto* row = new QWidget(_effectStackList);
        auto* rowLayout = new QHBoxLayout(row);
        rowLayout->setContentsMargins(6, 0, 6, 0);
        rowLayout->setSpacing(6);

        auto* label = new QLabel(name + " (" + kind + ")", row);
        label->setStyleSheet("color: #e6e6e6;");
        auto* removeBtn = new QPushButton("x", row);
        removeBtn->setFixedSize(20, 20);
        removeBtn->setStyleSheet("QPushButton { color: #e6e6e6; background: #3a3a3a; border: 1px solid #4a4a4a; }");

        connect(removeBtn, &QPushButton::clicked, this, [this, i]() {
            removeEffectAt(static_cast<int>(i));
        });

        rowLayout->addWidget(label, 1);
        rowLayout->addWidget(removeBtn, 0);
        row->setLayout(rowLayout);

        _effectStackList->addItem(item);
        _effectStackList->setItemWidget(item, row);
    }
}

void UiPanel::removeSelectedEffect()
{
    if (_activeInputIndex < 0 || _activeInputIndex >= static_cast<int>(_effectsByInput.size())) {
        return;
    }
    if (_activeEffectIndex < 0 || _activeEffectIndex >= static_cast<int>(_effectsByInput[_activeInputIndex].size())) {
        return;
    }

    _effectsByInput[_activeInputIndex].erase(_effectsByInput[_activeInputIndex].begin() + _activeEffectIndex);
    _activeEffectIndex = -1;
    refreshEffectStackList();
    refreshPreviewFromUi();
}

void UiPanel::removeEffectAt(int index)
{
    if (_activeInputIndex < 0 || _activeInputIndex >= static_cast<int>(_effectsByInput.size())) {
        return;
    }
    if (index < 0 || index >= static_cast<int>(_effectsByInput[_activeInputIndex].size())) {
        return;
    }
    _effectsByInput[_activeInputIndex].erase(_effectsByInput[_activeInputIndex].begin() + index);
    if (_activeEffectIndex == index) {
        _activeEffectIndex = -1;
    } else if (_activeEffectIndex > index) {
        _activeEffectIndex -= 1;
    }
    refreshEffectStackList();
    refreshPreviewFromUi();
}

void UiPanel::renderVideo()
{
    if (_inputs.empty()) {
        VC_LOG_DEBUG("[UI] Render: no inputs.");
        return;
    }

    const QString path = QFileDialog::getSaveFileName(this, "Render Video", "output.mp4", "Video Files (*.mp4)");
    if (path.isEmpty()) {
        return;
    }

    refreshPreviewFromUi();
    _core->generateVideo(path.toStdString());
}

bool UiPanel::buildStack(nlohmann::json::array_t& outStack)
{
    // Create the full instruction stack for all inputs + effects.
    const std::unordered_set<QString> supportedInputs = {
        "Image",
        "Video",
        "WebImage",
        "Text",
        "Rectangle",
        "Circle",
        "Line",
    };

    for (size_t i = 0; i < _inputs.size(); ++i) {
        if (!appendInputCreate(_inputs[i], static_cast<int>(i), outStack)) {
            return false;
        }

        const QString inputName = upperFirst(QString::fromStdString(_inputs[i].value("name", "")));
        if (!supportedInputs.count(inputName)) {
            VC_LOG_DEBUG("[UI] Unsupported input: " + inputName.toStdString());
            return false;
        }

        if (i < _effectsByInput.size()) {
            for (size_t e = 0; e < _effectsByInput[i].size(); ++e) {
                const auto& eff = _effectsByInput[i][e];
                const bool isActiveEdit = static_cast<int>(i) == _activeInputIndex &&
                                          static_cast<int>(e) == _activeEffectIndex &&
                                          _uiEffect.is_object();
                const auto& effSrc = isActiveEdit ? _uiEffect : eff;
                appendEffectApply(effSrc, static_cast<int>(i), outStack);
            }
        }
    }

    // Draft effect (preview) when not editing an existing stack entry
    if (_uiEffect.is_object() &&
        _activeInputIndex >= 0 &&
        _activeInputIndex < static_cast<int>(_inputs.size()) &&
        _activeEffectIndex < 0) {
        appendEffectApply(_uiEffect, _activeInputIndex, outStack);
    }

    return true;
}

bool UiPanel::appendInputCreate(const nlohmann::json& inputDef, int index, nlohmann::json::array_t& outStack)
{
    // Convert an input definition into a Create action.
    nlohmann::json::object_t createArgs;
    if (!buildCreateArgs(inputDef, createArgs)) {
        return false;
    }

    const QString inputName = upperFirst(QString::fromStdString(inputDef.value("name", "")));
    outStack.push_back(
        {
            {"action", "Create"},
            {"type", inputName.toStdString()},
            {"args", createArgs},
        }
    );
    return true;
}

void UiPanel::appendEffectApply(const nlohmann::json& effDef, int inputIndex, nlohmann::json::array_t& outStack)
{
    // Convert an effect definition into an Apply action.
    const QString ename = upperFirst(QString::fromStdString(effDef.value("name", "")));
    const QString ekind = QString::fromStdString(effDef.value("kind", ""));

    nlohmann::json::object_t effectArgs;
    for (const auto& p : effDef["params"]) {
        if (!p.contains("name") || !p.contains("value")) {
            continue;
        }
        const std::string pname = p["name"].get<std::string>();
        const std::string ptype = p.value("type", "Any");
        auto pval = p["value"];

        if (pval.is_null()) {
            const auto t = QString::fromStdString(ptype).toLower();
            if (t.contains("bool")) {
                pval = false;
            } else if (t.contains("float") || t.contains("number") || t.contains("int")) {
                pval = 1.0;
            } else if (t.contains("str")) {
                pval = "";
            }
        }

        if (ename == "Position" && (pname == "x" || pname == "y")) {
            if (pval.is_number()) {
                pval = pval.get<double>() * WORLD_TO_SCREEN_RATIO;
            }
        }

        effectArgs[pname] = pval;
    }
    effectArgs["start"] = 0;
    effectArgs["duration"] = 1;

    outStack.push_back(
        {
            {"action", "Apply"},
            {"input", inputIndex},
            {"name", ename.toStdString()},
            {"type", ekind == "vertex" ? "VertexShader" : "FragmentShader"},
            {"args", effectArgs},
        }
    );
}

void UiPanel::fillEditorFromEffect(QWidget* editor, const nlohmann::json& effectParams, const QString& pname)
{
    // Restore stored effect values into the UI editor widget.
    for (const auto& v : effectParams) {
        if (!v.contains("name") || v["name"].get<std::string>() != pname.toStdString()) {
            continue;
        }
        if (!v.contains("value")) {
            continue;
        }
        const auto& val = v["value"];
        if (auto* spin = qobject_cast<QSpinBox*>(editor)) {
            if (val.is_number_integer()) {
                spin->setValue(val.get<int>());
            }
        } else if (auto* dspin = qobject_cast<QDoubleSpinBox*>(editor)) {
            if (val.is_number()) {
                dspin->setValue(val.get<double>());
            }
        } else if (auto* box = qobject_cast<QCheckBox*>(editor)) {
            if (val.is_boolean()) {
                box->setChecked(val.get<bool>());
            }
        } else if (auto* edit = qobject_cast<QLineEdit*>(editor)) {
            if (val.is_string()) {
                edit->setText(QString::fromStdString(val.get<std::string>()));
            }
        }
    }
}

bool UiPanel::buildCreateArgs(const nlohmann::json& inputDef, nlohmann::json::object_t& outArgs)
{
    if (!inputDef.contains("params")) {
        return true;
    }
    for (const auto& p : inputDef["params"]) {
        if (!p.contains("name") || !p.contains("value")) {
            continue;
        }
        const std::string pname = p["name"].get<std::string>();
        const auto& pval = p["value"];
        if (pname == "filepath") {
            if (!pval.is_string() || pval.get<std::string>().empty()) {
                VC_LOG_DEBUG("[UI] Missing filepath for input");
                return false;
            }
            const QString qpath = QString::fromStdString(pval.get<std::string>());
            QFileInfo info(qpath);
            if (!info.exists()) {
                VC_LOG_DEBUG("[UI] Invalid filepath: " + qpath.toStdString());
                return false;
            }
        }
        outArgs[pname] = pval;
    }
    return true;
}


} // namespace VC
