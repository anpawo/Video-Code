/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** UiPanel
*/

#include "window/UiPanel.hpp"

#include <algorithm>
#include <cmath>
#include <opencv2/videoio.hpp>
#include <QApplication>
#include <QCheckBox>
#include <QDoubleSpinBox>
#include <QFileDialog>
#include <QFileInfo>
#include <QFormLayout>
#include <QFrame>
#include <QGridLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QListWidget>
#include <QLineEdit>
#include <QElapsedTimer>
#include <QPixmap>
#include <QProgressDialog>
#include <QPushButton>
#include <QScrollArea>
#include <QShortcut>
#include <QSizePolicy>
#include <QSpinBox>
#include <QSplitter>
#include <QResizeEvent>
#include <QSignalBlocker>
#include <QTimer>
#include <QTreeWidget>
#include <QTreeWidgetItem>
#include <QVBoxLayout>
#include <string>
#include <unordered_set>
#include <vector>
#include "core/Core.hpp"
#include "utils/Debug.hpp"
#include "window/EffectTimeline.hpp"

namespace VC
{

namespace
{
    constexpr double kWorldToScreenRatio = 120.0;
    constexpr int kSpinBoxMin = -100000;
    constexpr int kSpinBoxMax = 100000;
    constexpr double kDoubleSpinBoxMin = -100000.0;
    constexpr double kDoubleSpinBoxMax = 100000.0;
    constexpr int kUiDebounceMs = 120;
    constexpr int kLeftPaneMinWidth = 300;
    constexpr int kRightPaneMinWidth = 360;
    constexpr int kSplitterHandleWidth = 6;
    constexpr int kDefaultEffectFrames = 60;
    constexpr int kFallbackProjectFrames = 150;
    constexpr int kPlayheadRefreshMs = 33;
    constexpr const char* kKindInput = "input";
    constexpr const char* kKindVertex = "vertex";
    constexpr const char* kKindFragment = "fragment";
    constexpr const char* kKindTemplate = "template";
    constexpr const char* kKindHelper = "helper";
    constexpr const char* kRgbaEditorName = "rgbaEditor";
    constexpr const char* kRgbaChannelName = "rgbaChannel";

    QString upperFirstText(const QString& text)
    {
        if (text.isEmpty()) {
            return text;
        }
        QString out = text;
        out[0] = out[0].toUpper();
        return out;
    }

    const std::vector<QString>& supportedInputKinds()
    {
        static const std::vector<QString> supportedInputs = {
            "Video",
            "Image",
            "WebImage",
            "Text",
            "Rectangle",
            "Circle",
            "Line",
        };
        return supportedInputs;
    }

    bool isValidIndex(int index, size_t size)
    {
        return index >= 0 && static_cast<size_t>(index) < size;
    }

    template <typename T>
    bool isValidIndex(int index, const std::vector<T>& items)
    {
        return isValidIndex(index, items.size());
    }

    bool isEffectKind(const QString& kind)
    {
        return kind == kKindVertex || kind == kKindFragment;
    }

    bool isSupportedInput(const QString& inputName)
    {
        const QString canonicalName = upperFirstText(inputName);
        return std::find(supportedInputKinds().begin(), supportedInputKinds().end(), canonicalName) != supportedInputKinds().end();
    }

    nlohmann::json parseRgbaText(const QString& text)
    {
        QString cleaned = text.trimmed();
        if (cleaned.startsWith("(") && cleaned.endsWith(")")) {
            cleaned = cleaned.mid(1, cleaned.size() - 2);
        }
        if (cleaned.startsWith("[") && cleaned.endsWith("]")) {
            cleaned = cleaned.mid(1, cleaned.size() - 2);
        }

        const QStringList parts = cleaned.split(",", Qt::SkipEmptyParts);
        if (parts.size() != 4) {
            return text.toStdString();
        }

        nlohmann::json values = nlohmann::json::array();
        for (const QString& part : parts) {
            bool ok = false;
            const int value = part.trimmed().toInt(&ok);
            if (!ok) {
                return text.toStdString();
            }
            values.push_back(std::clamp(value, 0, 255));
        }
        return values;
    }

    QWidget* createRgbaEditor(const QString& defaultValue)
    {
        auto* container = new QWidget();
        container->setObjectName(kRgbaEditorName);

        auto* layout = new QGridLayout(container);
        layout->setContentsMargins(0, 0, 0, 0);
        layout->setHorizontalSpacing(8);
        layout->setVerticalSpacing(6);

        nlohmann::json rgba = parseRgbaText(defaultValue);
        std::array<int, 4> channels{255, 255, 255, 255};
        if (rgba.is_array() && rgba.size() == 4) {
            for (size_t i = 0; i < channels.size(); ++i) {
                channels[i] = std::clamp(rgba[i].get<int>(), 0, 255);
            }
        }

        static const std::array<const char*, 4> labels = {"R", "G", "B", "A"};
        for (size_t i = 0; i < labels.size(); ++i) {
            auto* spin = new QSpinBox(container);
            spin->setObjectName(kRgbaChannelName);
            spin->setProperty("channelIndex", static_cast<int>(i));
            spin->setRange(0, 255);
            spin->setValue(channels[i]);
            spin->setButtonSymbols(QAbstractSpinBox::NoButtons);
            spin->setAlignment(Qt::AlignCenter);
            spin->setMaximumWidth(72);

            auto* label = new QLabel(labels[i], container);
            label->setMinimumWidth(12);
            label->setAlignment(Qt::AlignCenter);

            const int row = static_cast<int>(i / 2);
            const int columnOffset = static_cast<int>(i % 2) * 2;
            layout->addWidget(label, row, columnOffset);
            layout->addWidget(spin, row, columnOffset + 1);
        }

        return container;
    }

    bool isRgbaEditor(QWidget* editor)
    {
        return editor && editor->objectName() == kRgbaEditorName;
    }

    nlohmann::json readRgbaEditorValue(QWidget* editor)
    {
        nlohmann::json rgba = nlohmann::json::array();
        if (!editor) {
            return rgba;
        }

        const auto channels = editor->findChildren<QSpinBox*>(kRgbaChannelName, Qt::FindDirectChildrenOnly);
        std::array<int, 4> values{255, 255, 255, 255};
        for (QSpinBox* spin : channels) {
            bool ok = false;
            const int index = spin->property("channelIndex").toInt(&ok);
            if (!ok || index < 0 || index >= static_cast<int>(values.size())) {
                continue;
            }
            values[index] = spin->value();
        }
        for (int value : values) {
            rgba.push_back(value);
        }
        return rgba;
    }

    void writeRgbaEditorValue(QWidget* editor, const nlohmann::json& value)
    {
        if (!editor || !value.is_array() || value.size() != 4) {
            return;
        }

        const auto channels = editor->findChildren<QSpinBox*>(kRgbaChannelName, Qt::FindDirectChildrenOnly);
        for (QSpinBox* spin : channels) {
            bool ok = false;
            const int index = spin->property("channelIndex").toInt(&ok);
            if (!ok || index < 0 || index >= 4 || !value[index].is_number_integer()) {
                continue;
            }
            spin->setValue(std::clamp(value[index].get<int>(), 0, 255));
        }
    }
} // namespace

static QWidget* createEditor(const QString& type, const QString& defaultValue)
{
    const QString t = type.toLower();
    if (t.contains("rgba")) {
        return createRgbaEditor(defaultValue);
    }

    if (t.contains("bool")) {
        auto* box = new QCheckBox();
        box->setChecked(defaultValue == "True" || defaultValue == "true");
        return box;
    }

    if (t.contains("int") && !t.contains("float")) {
        auto* spin = new QSpinBox();
        spin->setRange(kSpinBoxMin, kSpinBoxMax);
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
        spin->setRange(kDoubleSpinBoxMin, kDoubleSpinBoxMax);
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
        if (_currentKind == kKindInput) {
            addOrUpdateInput();
        } else if (isEffectKind(_currentKind)) {
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
        VC_LOG_DEBUG("[UI] Failed to run UI schema generator.");
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
        VC_LOG_DEBUG("[UI] Failed to parse UI schema JSON.");
        return nlohmann::json::object();
    }
}

void UiPanel::buildUi()
{
    setObjectName("editorRoot");

    auto* rootLayout = new QVBoxLayout(this);
    rootLayout->setContentsMargins(14, 14, 14, 14);
    rootLayout->setSpacing(12);

    auto* topBar = new QWidget(this);
    topBar->setObjectName("toolbarCard");
    auto* topLayout = new QHBoxLayout(topBar);
    topLayout->setContentsMargins(14, 12, 14, 12);
    topLayout->setSpacing(12);

    auto* title = new QLabel("VideoCode", topBar);
    title->setObjectName("appTitle");
    auto* subtitle = new QLabel("UI editor", topBar);
    subtitle->setObjectName("toolbarHint");

    auto* titleWrap = new QWidget(topBar);
    auto* titleWrapLayout = new QHBoxLayout(titleWrap);
    titleWrapLayout->setContentsMargins(0, 0, 0, 0);
    titleWrapLayout->setSpacing(10);
    titleWrapLayout->addWidget(title, 0);
    titleWrapLayout->addWidget(subtitle, 0);
    titleWrapLayout->addStretch(1);

    auto* renderBtn = new QPushButton("Render Video", topBar);
    renderBtn->setObjectName("primaryButton");
    connect(renderBtn, &QPushButton::clicked, this, &UiPanel::renderVideo);

    topLayout->addWidget(titleWrap, 1);
    topLayout->addWidget(renderBtn, 0);
    rootLayout->addWidget(topBar, 0);

    _effectTree = new QTreeWidget(this);
    _effectTree->setHeaderHidden(true);
    _effectTree->setUniformRowHeights(true);
    _effectTree->setMinimumWidth(240);

    auto* leftPane = new QWidget(this);
    _leftPane = leftPane;
    leftPane->setObjectName("sideCard");
    leftPane->setMinimumWidth(kLeftPaneMinWidth);
    auto* leftLayout = new QVBoxLayout(leftPane);
    leftLayout->setContentsMargins(14, 14, 14, 14);
    leftLayout->setSpacing(10);

    auto* inputLabel = new QLabel("Inputs", leftPane);
    inputLabel->setObjectName("sectionTitle");
    _inputList = new QListWidget(leftPane);
    _inputList->setMinimumHeight(150);

    auto* inputActions = new QWidget(leftPane);
    auto* inputActionsLayout = new QHBoxLayout(inputActions);
    inputActionsLayout->setContentsMargins(0, 0, 0, 0);
    inputActionsLayout->setSpacing(8);

    auto* newInputBtn = new QPushButton("New Input", inputActions);
    newInputBtn->setObjectName("secondaryButton");
    connect(newInputBtn, &QPushButton::clicked, this, [this]() {
        const QSignalBlocker blocker(_inputList);
        _inputList->setCurrentRow(-1);
        _activeInputIndex = -1;
        _isCreatingNewInput = true;
        _activeEffectIndex = -1;
        _uiEffect = nlohmann::json();
        refreshEffectStackList();

        if (_currentKind == kKindInput && !_currentName.isEmpty()) {
            showInspectorFor(_currentName, _currentParams);
        } else {
            showInspectorMessage("Create Input", "Pick an input type in the library, then configure it here.");
        }
        refreshStudioState();
    });

    auto* removeInputBtn = new QPushButton("Remove Input", inputActions);
    removeInputBtn->setObjectName("dangerButton");
    connect(removeInputBtn, &QPushButton::clicked, this, &UiPanel::removeSelectedInput);

    inputActionsLayout->addWidget(newInputBtn, 1);
    inputActionsLayout->addWidget(removeInputBtn, 1);

    auto* libraryLabel = new QLabel("Library", leftPane);
    libraryLabel->setObjectName("sectionTitle");

    leftLayout->addWidget(inputLabel);
    leftLayout->addWidget(_inputList);
    leftLayout->addWidget(inputActions);
    leftLayout->addSpacing(4);
    leftLayout->addWidget(libraryLabel);
    leftLayout->addWidget(_effectTree, 1);

    auto* previewPane = new QWidget(this);
    _previewPane = previewPane;
    previewPane->setObjectName("previewCard");
    auto* previewLayout = new QVBoxLayout(previewPane);
    previewLayout->setContentsMargins(14, 14, 14, 14);
    previewLayout->setSpacing(10);

    auto* previewLabel = new QLabel("Preview", previewPane);
    previewLabel->setObjectName("sectionTitle");

    auto* previewStage = new QWidget(previewPane);
    _previewStage = previewStage;
    previewStage->setObjectName("previewStage");
    previewStage->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    auto* previewStageLayout = new QVBoxLayout(previewStage);
    previewStageLayout->setContentsMargins(20, 20, 20, 20);
    previewStageLayout->setAlignment(Qt::AlignCenter);

    _preview->setAlignment(Qt::AlignCenter);
    _preview->setScaledContents(false);
    _preview->setObjectName("previewLabel");
    _preview->setText("Add an input to start previewing");
    previewStageLayout->addWidget(_preview, 0, Qt::AlignCenter);

    previewLayout->addWidget(previewLabel, 0);
    previewLayout->addWidget(previewStage, 1);

    auto* timelinePane = new QWidget(this);
    timelinePane->setObjectName("timelineCard");
    auto* timelineLayout = new QVBoxLayout(timelinePane);
    timelineLayout->setContentsMargins(14, 14, 14, 14);
    timelineLayout->setSpacing(10);

    auto* timelineHeader = new QWidget(timelinePane);
    auto* timelineHeaderLayout = new QHBoxLayout(timelineHeader);
    timelineHeaderLayout->setContentsMargins(0, 0, 0, 0);
    timelineHeaderLayout->setSpacing(10);
    auto* timelineLabel = new QLabel("Timeline", timelinePane);
    timelineLabel->setObjectName("sectionTitle");
    auto* timelineHint = new QLabel("frames", timelinePane);
    timelineHint->setObjectName("toolbarHint");

    _playPauseBtn = new QPushButton(timelinePane);
    _playPauseBtn->setObjectName("secondaryButton");
    _playPauseBtn->setFixedWidth(80);
    connect(_playPauseBtn, &QPushButton::clicked, this, &UiPanel::togglePlayPause);

    auto* gotoStartBtn = new QPushButton("|<", timelinePane);
    gotoStartBtn->setObjectName("secondaryButton");
    gotoStartBtn->setFixedWidth(36);
    connect(gotoStartBtn, &QPushButton::clicked, this, [this]() {
        if (_core) {
            _core->seekToFrame(0);
        }
    });

    _frameCounter = new QLabel("0 / 0", timelinePane);
    _frameCounter->setObjectName("toolbarHint");
    _frameCounter->setMinimumWidth(80);
    _frameCounter->setAlignment(Qt::AlignVCenter | Qt::AlignRight);

    timelineHeaderLayout->addWidget(timelineLabel, 0);
    timelineHeaderLayout->addWidget(timelineHint, 0);
    timelineHeaderLayout->addStretch(1);
    timelineHeaderLayout->addWidget(gotoStartBtn, 0);
    timelineHeaderLayout->addWidget(_playPauseBtn, 0);
    timelineHeaderLayout->addWidget(_frameCounter, 0);

    _timeline = new EffectTimeline(timelinePane);
    timelineLayout->addWidget(timelineHeader, 0);
    timelineLayout->addWidget(_timeline, 1);

    auto* centerSplitter = new QSplitter(Qt::Vertical, this);
    _centerSplitter = centerSplitter;
    centerSplitter->setHandleWidth(kSplitterHandleWidth);
    centerSplitter->setChildrenCollapsible(false);
    centerSplitter->addWidget(previewPane);
    centerSplitter->addWidget(timelinePane);
    centerSplitter->setStretchFactor(0, 3);
    centerSplitter->setStretchFactor(1, 1);
    centerSplitter->setSizes({680, 240});

    _inspector = new QWidget(this);
    _inspectorForm = new QFormLayout(_inspector);
    _inspectorForm->setContentsMargins(10, 10, 10, 10);
    _inspectorForm->setSpacing(10);

    _inspectorScroll = new QScrollArea(this);
    _inspectorScroll->setWidgetResizable(true);
    _inspectorScroll->setWidget(_inspector);
    _inspectorScroll->setMinimumWidth(280);

    auto* rightPane = new QWidget(this);
    _rightPane = rightPane;
    rightPane->setObjectName("sideCard");
    rightPane->setMinimumWidth(kRightPaneMinWidth);
    auto* rightLayout = new QVBoxLayout(rightPane);
    rightLayout->setContentsMargins(14, 14, 14, 14);
    rightLayout->setSpacing(10);

    auto* effectLabel = new QLabel("Effect Stack", rightPane);
    effectLabel->setObjectName("sectionTitle");
    _effectStackList = new QListWidget(rightPane);
    _effectStackList->setMinimumHeight(150);

    auto* removeEffectBtn = new QPushButton("Remove Effect", rightPane);
    removeEffectBtn->setObjectName("dangerButton");
    connect(removeEffectBtn, &QPushButton::clicked, this, &UiPanel::removeSelectedEffect);

    rightLayout->addWidget(effectLabel);
    rightLayout->addWidget(_effectStackList);
    rightLayout->addWidget(removeEffectBtn);
    rightLayout->addWidget(_inspectorScroll, 1);

    auto* splitter = new QSplitter(Qt::Horizontal, this);
    _splitter = splitter;
    splitter->setHandleWidth(kSplitterHandleWidth);
    splitter->setChildrenCollapsible(false);
    splitter->addWidget(leftPane);
    splitter->addWidget(centerSplitter);
    splitter->addWidget(rightPane);
    splitter->setStretchFactor(0, 0);
    splitter->setStretchFactor(1, 1);
    splitter->setStretchFactor(2, 0);
    splitter->setSizes({kLeftPaneMinWidth, 980, kRightPaneMinWidth});

    rootLayout->addWidget(splitter, 1);

    setStyleSheet(
        "QWidget#editorRoot {"
        "  background: #15171b;"
        "}"
        "QWidget {"
        "  font-family: 'IBM Plex Sans', 'Segoe UI', 'Helvetica Neue', sans-serif;"
        "  font-size: 12px;"
        "  color: #eceef0;"
        "}"
        "QWidget#toolbarCard, QWidget#sideCard, QWidget#previewCard, QWidget#timelineCard {"
        "  background: #1c1f24;"
        "  border: 1px solid #2b3138;"
        "  border-radius: 16px;"
        "}"
        "QWidget#timelineCard {"
        "  background: #15171b;"
        "}"
        "QWidget#previewCard {"
        "  background: #1a1c20;"
        "}"
        "QWidget#previewStage {"
        "  background: qradialgradient(cx:0.5, cy:0.4, radius:0.9, stop:0 #22262d, stop:1 #0d0f12);"
        "  border: 1px solid #2f353d;"
        "  border-radius: 14px;"
        "}"
        "QLabel#appTitle {"
        "  color: #fafbfc;"
        "  font-size: 20px;"
        "  font-weight: 700;"
        "}"
        "QLabel#toolbarHint {"
        "  color: #8c959f;"
        "}"
        "QLabel#sectionTitle {"
        "  color: #cdd3d8;"
        "  font-size: 11px;"
        "  font-weight: 700;"
        "  letter-spacing: 0.9px;"
        "  text-transform: uppercase;"
        "}"
        "QLabel#previewLabel {"
        "  color: #7f8993;"
        "}"
        "QTreeWidget, QListWidget {"
        "  background: #111317;"
        "  border: 1px solid #2a3037;"
        "  border-radius: 12px;"
        "  padding: 6px;"
        "  outline: none;"
        "}"
        "QTreeWidget::item, QListWidget::item {"
        "  padding: 7px 9px;"
        "  margin: 2px 0;"
        "  border-radius: 7px;"
        "}"
        "QTreeWidget::item:selected, QListWidget::item:selected {"
        "  background: #2d6cdf;"
        "  color: #ffffff;"
        "}"
        "QTreeWidget::item:hover, QListWidget::item:hover {"
        "  background: #1b2027;"
        "}"
        "QScrollArea {"
        "  background: transparent;"
        "  border: 1px solid #2a3037;"
        "  border-radius: 12px;"
        "}"
        "QScrollArea QWidget {"
        "  background: transparent;"
        "}"
        "QPushButton {"
        "  background: #242a31;"
        "  border: 1px solid #38414a;"
        "  border-radius: 10px;"
        "  padding: 8px 12px;"
        "}"
        "QPushButton:hover {"
        "  background: #2b323a;"
        "}"
        "QPushButton#primaryButton {"
        "  background: #2d6cdf;"
        "  border: 1px solid #2a62ca;"
        "  color: #ffffff;"
        "  font-weight: 700;"
        "}"
        "QPushButton#primaryButton:hover {"
        "  background: #3a78ea;"
        "}"
        "QPushButton#secondaryButton {"
        "  background: #1f2833;"
        "  border: 1px solid #30465d;"
        "  color: #d8e8f6;"
        "}"
        "QPushButton#secondaryButton:hover {"
        "  background: #253140;"
        "}"
        "QPushButton#dangerButton {"
        "  background: #462626;"
        "  border: 1px solid #663333;"
        "  color: #f1cece;"
        "}"
        "QPushButton#dangerButton:hover {"
        "  background: #562e2e;"
        "}"
        "QLineEdit, QSpinBox, QDoubleSpinBox {"
        "  background: #101216;"
        "  border: 1px solid #2b3138;"
        "  border-radius: 8px;"
        "  padding: 7px 9px;"
        "}"
        "QCheckBox {"
        "  spacing: 8px;"
        "}"
        "QSplitter::handle {"
        "  background: transparent;"
        "}"
        "QScrollBar:vertical {"
        "  background: transparent;"
        "  width: 10px;"
        "}"
        "QScrollBar::handle:vertical {"
        "  background: #313840;"
        "  border-radius: 5px;"
        "  min-height: 24px;"
        "}"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {"
        "  height: 0px;"
        "}"
        "QScrollBar:horizontal {"
        "  background: transparent;"
        "  height: 10px;"
        "}"
        "QScrollBar::handle:horizontal {"
        "  background: #313840;"
        "  border-radius: 5px;"
        "  min-width: 24px;"
        "}"
        "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {"
        "  width: 0px;"
        "}"
    );

    _uiDebounce = new QTimer(this);
    _uiDebounce->setSingleShot(true);
    connect(_uiDebounce, &QTimer::timeout, this, &UiPanel::refreshPreviewFromUi);

    if (_timeline) {
        connect(_timeline, &EffectTimeline::clipSelected, this, &UiPanel::onTimelineClipSelected);
        connect(_timeline, &EffectTimeline::playheadScrubbed, this, &UiPanel::onTimelineScrubbed);
    }

    _playheadTimer = new QTimer(this);
    _playheadTimer->setInterval(kPlayheadRefreshMs);
    connect(_playheadTimer, &QTimer::timeout, this, [this]() {
        if (_timeline && _core) {
            _timeline->setCurrentFrame(_core->currentFrame());
        }
        if (_frameCounter && _core) {
            _frameCounter->setText(
                QString("%1 / %2").arg(_core->currentFrame()).arg(_core->frameCount())
            );
        }
        updatePlayPauseButton();
    });
    _playheadTimer->start();

    updatePlayPauseButton();

    _schema = loadUiSchema();
    populateEffectTree(_schema);
    showInspectorMessage("Create Input", "Pick an input type in the library, then configure it here.");
    updatePreviewSize();
    refreshStudioState();

    connect(
        _effectTree,
        &QTreeWidget::itemClicked,
        this,
        [this](QTreeWidgetItem* item, int) {
            if (!item->parent()) {
                item->setExpanded(!item->isExpanded());
                return;
            }
            const QString displayName = item->text(0);
            const auto paramsJson = item->data(0, Qt::UserRole).toString();
            const QString kind = item->data(0, Qt::UserRole + 1).toString();
            const QString rawName = item->data(0, Qt::UserRole + 2).toString();
            const QString name = rawName.isEmpty() ? displayName : rawName;
            try {
                const auto params = nlohmann::json::parse(paramsJson.toStdString());
                _currentKind = kind;
                _currentName = name;
                _currentParams = params;
                _activeEffectIndex = -1;
                if (_currentKind == kKindInput) {
                    const QSignalBlocker blocker(_inputList);
                    _inputList->setCurrentRow(-1);
                    _activeInputIndex = -1;
                    _isCreatingNewInput = true;
                    const size_t defaultInputDuration = std::max<size_t>(timelineFrameCount(), static_cast<size_t>(kDefaultEffectFrames));
                    _uiInput = {
                        {"name", _currentName.toStdString()},
                        {"params", nlohmann::json::array()},
                        {"startFrame", static_cast<size_t>(0)},
                        {"duration", defaultInputDuration},
                    };
                    _uiEffect = nlohmann::json();
                    refreshEffectStackList();
                } else if (isEffectKind(_currentKind) && isValidIndex(_activeInputIndex, _effectsByInput)) {
                    const size_t defaultDuration = std::max<size_t>(timelineFrameCount(), kDefaultEffectFrames);
                    _uiEffect = {
                        {"name", _currentName.toStdString()},
                        {"kind", _currentKind.toStdString()},
                        {"params", nlohmann::json::array()},
                        {"startFrame", static_cast<size_t>(0)},
                        {"duration", defaultDuration},
                    };
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
                showInspectorFor(displayName, params);
                refreshStudioState();
            } catch (...) {
                clearInspector();
                refreshStudioState();
            }
        }
    );

    connect(_inputList, &QListWidget::currentRowChanged, this, [this](int row) {
        _activeInputIndex = row;
        _isCreatingNewInput = false;
        _activeEffectIndex = -1;
        _uiEffect = nlohmann::json();
        refreshEffectStackList();

        if (!isValidIndex(row, _inputs)) {
            if (_currentKind == kKindInput && !_currentName.isEmpty()) {
                showInspectorFor(_currentName, _currentParams);
            } else {
                showInspectorMessage("Create Input", "Pick an input type in the library, then configure it here.");
            }
            refreshStudioState();
            return;
        }

        _uiInput = _inputs[row];
        _currentKind = kKindInput;
        _currentName = QString::fromStdString(_uiInput.value("name", ""));
        _currentParams = schemaParamsFor(_currentName, _currentKind);
        showInspectorFor(_currentName, _currentParams);
        refreshStudioState();
    });

    connect(_effectStackList, &QListWidget::currentRowChanged, this, [this](int row) {
        _activeEffectIndex = row;
        if (!isValidIndex(_activeInputIndex, _effectsByInput)) {
            return;
        }
        if (!isValidIndex(row, _effectsByInput[_activeInputIndex])) {
            return;
        }
        _uiEffect = _effectsByInput[_activeInputIndex][row];
        _currentKind = QString::fromStdString(_uiEffect.value("kind", ""));
        _currentName = QString::fromStdString(_uiEffect.value("name", ""));
        _currentParams = schemaParamsFor(_currentName, _currentKind);
        showInspectorFor(_currentName, _currentParams);
        refreshStudioState();
    });
}

void UiPanel::resizeEvent(QResizeEvent* event)
{
    QWidget::resizeEvent(event);
    updatePreviewSize();
}

void UiPanel::updatePreviewSize()
{
    if (!_preview || !_previewStage) {
        return;
    }

    const int sceneW = _core ? _core->sceneWidth() : 1920;
    const int sceneH = _core ? _core->sceneHeight() : 1080;
    if (sceneW <= 0 || sceneH <= 0) {
        return;
    }

    const QMargins margins = _previewStage->contentsMargins();
    const QSize stageSize = _previewStage->size();
    const int maxW = std::max(0, stageSize.width() - margins.left() - margins.right() - 56);
    const int maxH = std::max(0, stageSize.height() - margins.top() - margins.bottom() - 56);

    if (maxW == 0 || maxH == 0) {
        return;
    }

    const double sceneAspect = static_cast<double>(sceneW) / static_cast<double>(sceneH);
    int targetW = maxW;
    int targetH = static_cast<int>(targetW / sceneAspect);
    if (targetH > maxH) {
        targetH = maxH;
        targetW = static_cast<int>(targetH * sceneAspect);
    }

    _preview->setFixedSize(targetW, targetH);
}

void UiPanel::showInspectorMessage(const QString& title, const QString& body)
{
    clearInspector();
    if (!_inspectorForm) {
        return;
    }

    auto* titleLabel = new QLabel(title, _inspector);
    QFont titleFont = titleLabel->font();
    titleFont.setBold(true);
    titleFont.setPointSize(titleFont.pointSize() + 2);
    titleLabel->setFont(titleFont);

    auto* bodyLabel = new QLabel(body, _inspector);
    bodyLabel->setWordWrap(true);
    bodyLabel->setStyleSheet("color: #a9b1bb; line-height: 1.4;");

    _inspectorForm->addRow(titleLabel);
    _inspectorForm->addRow(bodyLabel);
}

QString UiPanel::inputListLabel(const nlohmann::json& inputDef) const
{
    const QString inputName = upperFirst(QString::fromStdString(inputDef.value("name", "")));
    const auto params = inputDef.value("params", nlohmann::json::array());

    if (!params.is_array()) {
        return inputName;
    }

    for (const auto& param : params) {
        if (!param.contains("name") || param["name"] != "filepath" || !param.contains("value") || !param["value"].is_string()) {
            continue;
        }

        const QString filepath = QString::fromStdString(param["value"].get<std::string>());
        const QString filename = QFileInfo(filepath).fileName();
        if (!filename.isEmpty()) {
            return inputName + " | " + filename;
        }
    }

    return inputName;
}

QString UiPanel::fileDialogFilterForInput(const QString& inputName) const
{
    const QString canonicalName = upperFirst(inputName);
    if (canonicalName == "Video") {
        return "Videos (*.mp4 *.mov *.avi *.mkv *.m4v *.webm);;All Files (*)";
    }
    if (canonicalName == "Image") {
        return "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;All Files (*)";
    }
    return "All Files (*)";
}

nlohmann::json UiPanel::schemaParamsFor(const QString& name, const QString& kind) const
{
    if (!_schema.is_object()) {
        return nlohmann::json::array();
    }

    const auto findByName = [&name](const nlohmann::json& entries) -> nlohmann::json {
        if (!entries.is_array()) {
            return nlohmann::json::array();
        }
        for (const auto& entry : entries) {
            if (QString::fromStdString(entry.value("name", "")) == name) {
                return entry.value("params", nlohmann::json::array());
            }
        }
        return nlohmann::json::array();
    };

    if (kind == kKindInput) {
        return findByName(_schema.value("inputs", nlohmann::json::array()));
    }
    if (kind == kKindVertex || kind == kKindFragment) {
        const auto shaders = _schema.value("shaders", nlohmann::json::object());
        const auto key = kind == kKindVertex ? "vertex" : "fragment";
        return findByName(shaders.value(key, nlohmann::json::array()));
    }
    if (kind == kKindTemplate) {
        return findByName(_schema.value("templates", nlohmann::json::array()));
    }
    if (kind == kKindHelper) {
        return findByName(_schema.value("helpers", nlohmann::json::array()));
    }
    return nlohmann::json::array();
}

void UiPanel::refreshStudioState()
{
    if (_preview) {
        if (_inputs.empty() && !(_currentKind == kKindInput && _uiInput.is_object())) {
            _preview->setPixmap(QPixmap());
            _preview->setText("Add an input to start previewing");
        } else {
            _preview->setText(QString());
        }
    }
    refreshTimelineView();
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
        if (kind == kKindInput) {
            for (const QString& supportedName : supportedInputKinds()) {
                for (const auto& e : entries) {
                    if (!e.contains("name")) {
                        continue;
                    }
                    const QString rawName = QString::fromStdString(e["name"].get<std::string>());
                    if (upperFirstText(rawName) != supportedName) {
                        continue;
                    }
                    auto* child = new QTreeWidgetItem(category);
                    child->setText(0, supportedName);
                    if (e.contains("params")) {
                        child->setData(0, Qt::UserRole, QString::fromStdString(e["params"].dump()));
                    }
                    child->setData(0, Qt::UserRole + 1, kind);
                    child->setData(0, Qt::UserRole + 2, rawName);
                    break;
                }
            }
            return;
        }

        for (const auto& e : entries) {
            if (!e.contains("name")) {
                continue;
            }
            const QString entryName = QString::fromStdString(e["name"].get<std::string>());
            auto* child = new QTreeWidgetItem(category);
            child->setText(0, entryName);
            if (e.contains("params")) {
                child->setData(0, Qt::UserRole, QString::fromStdString(e["params"].dump()));
            }
            child->setData(0, Qt::UserRole + 1, kind);
        }
    };

    addEntries(addCategory("Inputs"), schema.value("inputs", nlohmann::json::array()), kKindInput);
    if (schema.contains("shaders")) {
        const auto shaders = schema["shaders"];
        addEntries(addCategory("Shaders: Vertex"), shaders.value("vertex", nlohmann::json::array()), kKindVertex);
        addEntries(addCategory("Shaders: Fragment"), shaders.value("fragment", nlohmann::json::array()), kKindFragment);
    }
    addEntries(addCategory("Templates"), schema.value("templates", nlohmann::json::array()), kKindTemplate);
    addEntries(addCategory("Input Helpers"), schema.value("helpers", nlohmann::json::array()), kKindHelper);
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
    _lifespanStartSpin = nullptr;
    _lifespanDurationSpin = nullptr;
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

    if (_currentKind == kKindTemplate || _currentKind == kKindHelper) {
        auto* note = new QLabel("Not supported in live preview yet.");
        _inspectorForm->addRow(note);
        return;
    }

    const bool hasLifespan = _currentKind == kKindInput || isEffectKind(_currentKind);
    if (hasLifespan) {
        const nlohmann::json& source = _currentKind == kKindInput ? _uiInput : _uiEffect;
        const size_t defaultDuration = std::max<size_t>(timelineFrameCount(), static_cast<size_t>(kDefaultEffectFrames));
        const size_t startVal = source.is_object() ? source.value("startFrame", static_cast<size_t>(0)) : 0;
        const size_t durationVal = source.is_object() ? source.value("duration", defaultDuration) : defaultDuration;

        _lifespanStartSpin = new QSpinBox(_inspector);
        _lifespanStartSpin->setRange(0, kSpinBoxMax);
        _lifespanStartSpin->setValue(static_cast<int>(startVal));
        _lifespanStartSpin->setSuffix(" f");

        _lifespanDurationSpin = new QSpinBox(_inspector);
        _lifespanDurationSpin->setRange(1, kSpinBoxMax);
        _lifespanDurationSpin->setValue(static_cast<int>(std::max<size_t>(durationVal, 1)));
        _lifespanDurationSpin->setSuffix(" f");

        connect(_lifespanStartSpin, qOverload<int>(&QSpinBox::valueChanged), this, &UiPanel::scheduleUiRefresh);
        connect(_lifespanDurationSpin, qOverload<int>(&QSpinBox::valueChanged), this, &UiPanel::scheduleUiRefresh);

        _inspectorForm->addRow("Start frame", _lifespanStartSpin);
        _inspectorForm->addRow("Duration", _lifespanDurationSpin);

        auto* sep = new QFrame(_inspector);
        sep->setFrameShape(QFrame::HLine);
        sep->setStyleSheet("color: #2a3037;");
        _inspectorForm->addRow(sep);
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
                const QString path = QFileDialog::getOpenFileName(
                    this,
                    "Select File",
                    ".",
                    fileDialogFilterForInput(_currentName)
                );
                if (path.isEmpty()) {
                    return;
                }
                line->setText(path);

                // For Video inputs, probe the file to set the default duration to its frame count.
                if (upperFirst(_currentName) == "Video" && _lifespanDurationSpin) {
                    cv::VideoCapture cap(path.toStdString());
                    if (cap.isOpened()) {
                        const int nbFrames = static_cast<int>(cap.get(cv::CAP_PROP_FRAME_COUNT));
                        if (nbFrames > 0) {
                            _lifespanDurationSpin->setValue(nbFrames);
                        }
                    }
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

        if (_currentKind == kKindInput && isValidIndex(_activeInputIndex, _inputs) && _uiInput.is_object()) {
            fillEditorFromEffect(editor, _uiInput.value("params", nlohmann::json::array()), pname);
        } else if (_activeEffectIndex >= 0 && _uiEffect.is_object()) {
            fillEditorFromEffect(editor, _uiEffect.value("params", nlohmann::json::array()), pname);
        }

        if (auto* spin = qobject_cast<QSpinBox*>(editor)) {
            connect(spin, qOverload<int>(&QSpinBox::valueChanged), this, &UiPanel::scheduleUiRefresh);
        } else if (auto* dspin = qobject_cast<QDoubleSpinBox*>(editor)) {
            connect(dspin, qOverload<double>(&QDoubleSpinBox::valueChanged), this, &UiPanel::scheduleUiRefresh);
        } else if (auto* box = qobject_cast<QCheckBox*>(editor)) {
            connect(box, &QCheckBox::toggled, this, &UiPanel::scheduleUiRefresh);
        } else if (auto* edit = qobject_cast<QLineEdit*>(editor)) {
            connect(edit, &QLineEdit::textChanged, this, &UiPanel::scheduleUiRefresh);
        } else if (isRgbaEditor(editor)) {
            const auto channels = editor->findChildren<QSpinBox*>(kRgbaChannelName, Qt::FindDirectChildrenOnly);
            for (QSpinBox* channel : channels) {
                connect(channel, qOverload<int>(&QSpinBox::valueChanged), this, &UiPanel::scheduleUiRefresh);
            }
        }
    }

    if (_currentKind == kKindInput) {
        _addInputBtn = new QPushButton(isValidIndex(_activeInputIndex, _inputs) ? "Save Input" : "Add Input");
        connect(_addInputBtn, &QPushButton::clicked, this, &UiPanel::addOrUpdateInput);
        _inspectorForm->addRow(_addInputBtn);
    } else if (isEffectKind(_currentKind)) {
        const bool isEditingEffect = isValidIndex(_activeInputIndex, _effectsByInput) &&
                                     isValidIndex(_activeEffectIndex, _effectsByInput[_activeInputIndex]);
        auto* applyBtn = new QPushButton(isEditingEffect ? "Update Effect" : "Apply Effect");
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
        } else if (isRgbaEditor(editor)) {
            value = readRgbaEditorValue(editor);
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

    const size_t defaultDuration = std::max<size_t>(timelineFrameCount(), static_cast<size_t>(kDefaultEffectFrames));
    size_t startFrame = 0;
    size_t duration = defaultDuration;
    const nlohmann::json& prior = _currentKind == kKindInput ? _uiInput : _uiEffect;
    if (_lifespanStartSpin) {
        startFrame = static_cast<size_t>(std::max(0, _lifespanStartSpin->value()));
    } else if (prior.is_object()) {
        startFrame = prior.value("startFrame", startFrame);
    }
    if (_lifespanDurationSpin) {
        duration = static_cast<size_t>(std::max(1, _lifespanDurationSpin->value()));
    } else if (prior.is_object()) {
        duration = std::max<size_t>(prior.value("duration", duration), 1);
    }

    if (_currentKind == kKindInput) {
        _uiInput = {
            {"name", _currentName.toStdString()},
            {"params", params},
            {"startFrame", startFrame},
            {"duration", duration},
        };
    } else if (isEffectKind(_currentKind)) {
        _uiEffect = {
            {"name", _currentName.toStdString()},
            {"kind", _currentKind.toStdString()},
            {"params", params},
            {"startFrame", startFrame},
            {"duration", duration},
        };
    }
}

void UiPanel::scheduleUiRefresh()
{
    updateCurrentDefinitionFromInspector();

    // Live-commit edits of an existing effect so the timeline reflects start/duration immediately.
    if (isEffectKind(_currentKind) && _uiEffect.is_object() &&
        isValidIndex(_activeInputIndex, _effectsByInput) &&
        isValidIndex(_activeEffectIndex, _effectsByInput[_activeInputIndex])) {
        _effectsByInput[_activeInputIndex][_activeEffectIndex] = _uiEffect;
    }

    // Live-commit edits of an existing input for the timeline.
    if (_currentKind == kKindInput && _uiInput.is_object() && !_isCreatingNewInput &&
        isValidIndex(_activeInputIndex, _inputs)) {
        _inputs[_activeInputIndex] = _uiInput;
        if (auto* item = _inputList->item(_activeInputIndex)) {
            item->setText(inputListLabel(_uiInput));
        }
    }

    if (_uiDebounce) {
        _uiDebounce->start(kUiDebounceMs);
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
    if (!_core) {
        VC_LOG_DEBUG("[UI] No core available for preview.");
        return;
    }
    updateCurrentDefinitionFromInspector();

    const bool hasDraftInput = _currentKind == kKindInput && _uiInput.is_object();
    if (_inputs.empty() && !hasDraftInput) {
        VC_LOG_DEBUG("[UI] No inputs to render");
        _core->loadStack({});
        refreshStudioState();
        return;
    }

    if (_inputs.empty()) {
        _activeInputIndex = -1;
    } else if (!_isCreatingNewInput && !isValidIndex(_activeInputIndex, _inputs)) {
        _activeInputIndex = 0;
    }

    nlohmann::json::array_t stack;
    if (!buildStack(stack)) {
        return;
    }

    _core->loadStack(stack);
    VC_LOG_DEBUG("[UI] Stack loaded (Create+Apply)");
    refreshStudioState();
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

    if (!_isCreatingNewInput && isValidIndex(_activeInputIndex, _inputs)) {
        _inputs[_activeInputIndex] = _uiInput;
        if (auto* item = _inputList->item(_activeInputIndex)) {
            item->setText(inputListLabel(_uiInput));
        }
    } else {
        _inputs.push_back(_uiInput);
        _effectsByInput.emplace_back();
        _inputList->addItem(inputListLabel(_uiInput));
        _isCreatingNewInput = false;
        _activeInputIndex = static_cast<int>(_inputs.size()) - 1;
        _inputList->setCurrentRow(_activeInputIndex);
    }

    refreshPreviewFromUi();
    refreshStudioState();
}

void UiPanel::removeSelectedInput()
{
    if (!isValidIndex(_activeInputIndex, _inputs)) {
        return;
    }

    _inputs.erase(_inputs.begin() + _activeInputIndex);
    if (isValidIndex(_activeInputIndex, _effectsByInput)) {
        _effectsByInput.erase(_effectsByInput.begin() + _activeInputIndex);
    }

    delete _inputList->takeItem(_activeInputIndex);

    _uiInput = nlohmann::json();
    _uiEffect = nlohmann::json();
    _isCreatingNewInput = false;
    _activeEffectIndex = -1;

    if (_inputs.empty()) {
        _activeInputIndex = -1;
        refreshEffectStackList();
        showInspectorMessage("Create Input", "Pick an input type in the library, then configure it here.");
        refreshPreviewFromUi();
        refreshStudioState();
        return;
    }

    const int nextIndex = std::min(_activeInputIndex, static_cast<int>(_inputs.size()) - 1);
    _activeInputIndex = -1;
    _inputList->setCurrentRow(nextIndex);
    refreshPreviewFromUi();
    refreshStudioState();
}

void UiPanel::addOrUpdateEffect()
{
    updateCurrentDefinitionFromInspector();
    if (!_uiEffect.is_object()) {
        VC_LOG_DEBUG("[UI] Add effect: no effect selected.");
        return;
    }
    if (!isValidIndex(_activeInputIndex, _inputs)) {
        VC_LOG_DEBUG("[UI] Add effect: no active input.");
        return;
    }

    if (_effectsByInput.size() < _inputs.size()) {
        _effectsByInput.resize(_inputs.size());
    }

    const QString name = QString::fromStdString(_uiEffect.value("name", ""));
    const QString kind = QString::fromStdString(_uiEffect.value("kind", ""));

    // If a specific effect is selected, update it.
    if (isValidIndex(_activeEffectIndex, _effectsByInput[_activeInputIndex])) {
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
    refreshStudioState();
}

void UiPanel::refreshEffectStackList()
{
    if (!_effectStackList) {
        return;
    }
    _effectStackList->clear();
    if (!isValidIndex(_activeInputIndex, _effectsByInput)) {
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
        label->setStyleSheet("color: #cfd5da;");
        auto* removeBtn = new QPushButton("x", row);
        removeBtn->setFixedSize(20, 20);
        removeBtn->setObjectName("transportButton");

        connect(removeBtn, &QPushButton::clicked, this, [this, i]() {
            removeEffectAt(static_cast<int>(i));
        });

        rowLayout->addWidget(label, 1);
        rowLayout->addWidget(removeBtn, 0);
        row->setLayout(rowLayout);

        _effectStackList->addItem(item);
        _effectStackList->setItemWidget(item, row);
    }

    if (isValidIndex(_activeEffectIndex, _effectsByInput[_activeInputIndex])) {
        _effectStackList->setCurrentRow(_activeEffectIndex);
    }

    refreshStudioState();
}

void UiPanel::removeSelectedEffect()
{
    if (!isValidIndex(_activeInputIndex, _effectsByInput)) {
        return;
    }
    if (!isValidIndex(_activeEffectIndex, _effectsByInput[_activeInputIndex])) {
        return;
    }

    _effectsByInput[_activeInputIndex].erase(_effectsByInput[_activeInputIndex].begin() + _activeEffectIndex);
    _activeEffectIndex = -1;
    _uiEffect = nlohmann::json();
    refreshEffectStackList();
    if (isValidIndex(_activeInputIndex, _inputs)) {
        _uiInput = _inputs[_activeInputIndex];
        _currentKind = kKindInput;
        _currentName = QString::fromStdString(_uiInput.value("name", ""));
        _currentParams = schemaParamsFor(_currentName, _currentKind);
        showInspectorFor(_currentName, _currentParams);
    }
    refreshPreviewFromUi();
    refreshStudioState();
}

void UiPanel::removeEffectAt(int index)
{
    if (!isValidIndex(_activeInputIndex, _effectsByInput)) {
        return;
    }
    if (!isValidIndex(index, _effectsByInput[_activeInputIndex])) {
        return;
    }
    _effectsByInput[_activeInputIndex].erase(_effectsByInput[_activeInputIndex].begin() + index);
    if (_activeEffectIndex == index) {
        _activeEffectIndex = -1;
        _uiEffect = nlohmann::json();
        if (isValidIndex(_activeInputIndex, _inputs)) {
            _uiInput = _inputs[_activeInputIndex];
            _currentKind = kKindInput;
            _currentName = QString::fromStdString(_uiInput.value("name", ""));
            _currentParams = schemaParamsFor(_currentName, _currentKind);
            showInspectorFor(_currentName, _currentParams);
        }
    } else if (_activeEffectIndex > index) {
        _activeEffectIndex -= 1;
    }
    refreshEffectStackList();
    refreshPreviewFromUi();
    refreshStudioState();
}

void UiPanel::renderVideo()
{
    if (_inputs.empty()) {
        VC_LOG_DEBUG("[UI] Render: no inputs.");
        return;
    }
    if (!_core) {
        VC_LOG_DEBUG("[UI] Render: core is null.");
        return;
    }

    const QString path = QFileDialog::getSaveFileName(this, "Render Video", "output.mp4", "Video Files (*.mp4)");
    if (path.isEmpty()) {
        return;
    }

    refreshPreviewFromUi();

    const size_t totalFrames = _core->frameCount();
    if (totalFrames == 0) {
        VC_LOG_DEBUG("[UI] Render: no frames to render.");
        return;
    }

    auto* dialog = new QProgressDialog("Rendering video...", "Cancel", 0, static_cast<int>(totalFrames), this);
    dialog->setWindowModality(Qt::WindowModal);
    dialog->setMinimumDuration(0);
    dialog->setAutoClose(false);
    dialog->setAutoReset(false);
    dialog->setValue(0);
    dialog->show();
    QApplication::processEvents();

    QElapsedTimer elapsed;
    elapsed.start();

    auto callback = [dialog, &elapsed](size_t current, size_t total) -> bool {
        if (dialog->wasCanceled()) {
            return false;
        }
        dialog->setValue(static_cast<int>(current));

        const qint64 ms = elapsed.elapsed();
        if (current > 0 && ms > 0) {
            const double fps = (current * 1000.0) / static_cast<double>(ms);
            const double remaining = (total - current) / std::max(fps, 0.001);
            const int remainSec = static_cast<int>(std::ceil(remaining));
            const int mm = remainSec / 60;
            const int ss = remainSec % 60;
            dialog->setLabelText(
                QString("Rendering frame %1 / %2  (%3 fps, ~%4:%5 remaining)")
                    .arg(current)
                    .arg(total)
                    .arg(QString::number(fps, 'f', 1))
                    .arg(mm, 2, 10, QChar('0'))
                    .arg(ss, 2, 10, QChar('0'))
            );
        } else {
            dialog->setLabelText(QString("Rendering frame %1 / %2").arg(current).arg(total));
        }

        QApplication::processEvents();
        return true;
    };

    const int rc = _core->generateVideo(path.toStdString(), callback);

    dialog->close();
    dialog->deleteLater();

    if (rc == 0) {
        VC_LOG_DEBUG("[UI] Render complete: " + path.toStdString());
    } else {
        VC_LOG_DEBUG("[UI] Render canceled.");
    }
}

bool UiPanel::buildStack(nlohmann::json::array_t& outStack)
{
    // Create the full instruction stack for all inputs + effects.
    for (size_t i = 0; i < _inputs.size(); ++i) {
        const bool isActiveInputEdit = _currentKind == kKindInput &&
                                       static_cast<int>(i) == _activeInputIndex &&
                                       _uiInput.is_object();
        const auto& inputSrc = isActiveInputEdit ? _uiInput : _inputs[i];

        if (!appendInputCreate(inputSrc, outStack)) {
            return false;
        }

        const QString inputName = upperFirst(QString::fromStdString(inputSrc.value("name", "")));
        if (!isSupportedInput(inputName)) {
            VC_LOG_DEBUG("[UI] Unsupported input: " + inputName.toStdString());
            return false;
        }

        appendInputLifespan(inputSrc, static_cast<int>(i), outStack);

        if (i < _effectsByInput.size()) {
            for (size_t e = 0; e < _effectsByInput[i].size(); ++e) {
                const auto& eff = _effectsByInput[i][e];
        const bool isActiveEdit = static_cast<int>(i) == _activeInputIndex &&
                                  !_isCreatingNewInput &&
                                  static_cast<int>(e) == _activeEffectIndex &&
                                  _uiEffect.is_object();
        const auto& effSrc = isActiveEdit ? _uiEffect : eff;
        appendEffectApply(effSrc, static_cast<int>(i), outStack);
            }
        }
    }

    const bool shouldPreviewDraftInput = _currentKind == kKindInput &&
                                         _uiInput.is_object() &&
                                         _isCreatingNewInput;
    if (shouldPreviewDraftInput) {
        const QString inputName = upperFirst(QString::fromStdString(_uiInput.value("name", "")));
        if (!isSupportedInput(inputName)) {
            VC_LOG_DEBUG("[UI] Unsupported input: " + inputName.toStdString());
            return false;
        }
        if (!appendInputCreate(_uiInput, outStack)) {
            return false;
        }
        appendInputLifespan(_uiInput, static_cast<int>(_inputs.size()), outStack);
    }

    // Draft effect (preview) when not editing an existing stack entry
    if (isEffectKind(_currentKind) &&
        _uiEffect.is_object() &&
        isValidIndex(_activeInputIndex, _inputs) &&
        _activeEffectIndex < 0) {
        appendEffectApply(_uiEffect, _activeInputIndex, outStack);
    }

    return true;
}

namespace
{
    void appendVertexFlag(int inputIndex, const std::string& transformName, size_t frame,
                          nlohmann::json::array_t& outStack)
    {
        outStack.push_back(
            {
                {"action", "Apply"},
                {"input", inputIndex},
                {"name", transformName},
                {"type", "VertexShader"},
                {"args", nlohmann::json::object_t{{"start", frame}, {"duration", static_cast<size_t>(1)}}},
            }
        );
    }
}

void UiPanel::appendInputLifespan(const nlohmann::json& inputDef, int inputIndex,
                                  nlohmann::json::array_t& outStack)
{
    const size_t startFrame = inputDef.value("startFrame", static_cast<size_t>(0));
    const size_t duration = inputDef.value("duration", static_cast<size_t>(0));

    if (startFrame > 0) {
        appendVertexFlag(inputIndex, "Hide", 0, outStack);
        appendVertexFlag(inputIndex, "Show", startFrame, outStack);
    }
    if (duration > 0) {
        appendVertexFlag(inputIndex, "Hide", startFrame + duration, outStack);
    }
}

bool UiPanel::appendInputCreate(const nlohmann::json& inputDef, nlohmann::json::array_t& outStack)
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
    const auto params = effDef.value("params", nlohmann::json::array());
    if (params.is_array()) {
        for (const auto& p : params) {
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
                    pval = pval.get<double>() * kWorldToScreenRatio;
                }
            }

            effectArgs[pname] = pval;
        }
    }
    const size_t startFrame = effDef.value("startFrame", static_cast<size_t>(0));
    const size_t duration = std::max<size_t>(effDef.value("duration", static_cast<size_t>(1)), 1);
    effectArgs["start"] = startFrame;
    effectArgs["duration"] = duration;

    outStack.push_back(
        {
            {"action", "Apply"},
            {"input", inputIndex},
            {"name", ename.toStdString()},
            {"type", ekind == kKindVertex ? "VertexShader" : "FragmentShader"},
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
        } else if (isRgbaEditor(editor)) {
            if (val.is_array() && val.size() == 4) {
                writeRgbaEditorValue(editor, val);
            } else if (val.is_string()) {
                writeRgbaEditorValue(editor, parseRgbaText(QString::fromStdString(val.get<std::string>())));
            }
        } else if (auto* edit = qobject_cast<QLineEdit*>(editor)) {
            if (val.is_string()) {
                edit->setText(QString::fromStdString(val.get<std::string>()));
            } else if (val.is_array() && val.size() == 4) {
                edit->setText(
                    QString("(%1, %2, %3, %4)")
                        .arg(val[0].get<int>())
                        .arg(val[1].get<int>())
                        .arg(val[2].get<int>())
                        .arg(val[3].get<int>())
                );
            }
        }
    }
}

size_t UiPanel::timelineFrameCount() const
{
    if (!_core) {
        return static_cast<size_t>(kFallbackProjectFrames);
    }
    const size_t coreFrames = _core->frameCount();
    if (coreFrames == 0) {
        return static_cast<size_t>(kFallbackProjectFrames);
    }
    return coreFrames;
}

void UiPanel::refreshTimelineView()
{
    if (!_timeline) {
        return;
    }
    const size_t current = _core ? _core->currentFrame() : 0;
    _timeline->setProject(_inputs, _effectsByInput, timelineFrameCount(), current);

    const int inputIdx = _activeInputIndex;
    const int effectIdx = _activeEffectIndex;
    if (isEffectKind(_currentKind) && isValidIndex(inputIdx, _effectsByInput) &&
        isValidIndex(effectIdx, _effectsByInput[inputIdx])) {
        _timeline->setSelection(inputIdx, effectIdx);
    } else {
        _timeline->setSelection(-1, -1);
    }
}

void UiPanel::onTimelineClipSelected(int inputIndex, int effectIndex)
{
    if (!isValidIndex(inputIndex, _effectsByInput)) {
        return;
    }
    if (!isValidIndex(effectIndex, _effectsByInput[inputIndex])) {
        return;
    }

    const QSignalBlocker inputBlocker(_inputList);
    _inputList->setCurrentRow(inputIndex);
    _activeInputIndex = inputIndex;
    _isCreatingNewInput = false;
    _activeEffectIndex = effectIndex;
    _uiEffect = _effectsByInput[inputIndex][effectIndex];
    _currentKind = QString::fromStdString(_uiEffect.value("kind", ""));
    _currentName = QString::fromStdString(_uiEffect.value("name", ""));
    _currentParams = schemaParamsFor(_currentName, _currentKind);

    refreshEffectStackList();
    showInspectorFor(_currentName, _currentParams);
    refreshStudioState();
    refreshTimelineView();
}

void UiPanel::onTimelineScrubbed(size_t frame)
{
    if (!_core) {
        return;
    }
    if (!_core->isPaused()) {
        _core->pause();
        updatePlayPauseButton();
    }
    _core->seekToFrame(frame);
}

void UiPanel::togglePlayPause()
{
    if (!_core) {
        return;
    }
    if (_core->frameCount() == 0) {
        return;
    }
    // When at the very last frame, restart from 0 before resuming playback.
    if (_core->isPaused() && _core->currentFrame() + 1 >= _core->frameCount()) {
        _core->seekToFrame(0);
    }
    _core->pause();
    updatePlayPauseButton();
}

void UiPanel::updatePlayPauseButton()
{
    if (!_playPauseBtn || !_core) {
        return;
    }
    _playPauseBtn->setText(_core->isPaused() ? "Play" : "Pause");
}

bool UiPanel::buildCreateArgs(const nlohmann::json& inputDef, nlohmann::json::object_t& outArgs)
{
    if (!inputDef.contains("params") || !inputDef["params"].is_array()) {
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
