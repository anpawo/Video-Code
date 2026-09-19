// The conversation, in the right-hand column.
//
// It sits in the dock rather than in a drawer because talking to the agent is not
// an interruption of editing — it IS editing here: what it answers with is code,
// and the code is the scene. So it gets a permanent column, and what used to live
// on the right (Properties, Effects) moves to the element you click.
//
// Only what it says is shown, not the tools it runs: the check on its work is the
// diff it leaves in the code pane.
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls

Item {
    id: root

    signal sent(string text)

    // The conversation, as it happens. Built by appending to a plain list
    // rather than by a model class: a turn is a handful of entries, and what
    // the pane needs from them is exactly what a ListView reads off an array.
    property var log: []

    // The answer being written, as an index into `log`, or -1 between turns.
    // Every sentence of one turn lands in that entry, so a question gets one
    // block back however many times the agent speaks.
    property int turn: -1

    // What the running counter reads. It only moves while the agent works, so
    // a finished answer keeps the time it took.
    property double now: 0

    function append(entry) {
        const grown = root.log.slice();
        grown.push(entry);
        root.log = grown;
    }

    function edit(index, changes) {
        const grown = root.log.slice();
        grown[index] = Object.assign({}, grown[index], changes);
        root.log = grown;
    }

    function say(text) {
        const line = { kind: "text", text: text };
        if (root.turn < 0)
            root.append({ who: "agent", body: [line], started: 0, ended: 0 });
        else
            root.edit(root.turn, { body: root.log[root.turn].body.concat([line]) });
    }

    function finish() {
        if (root.turn < 0)
            return;
        root.edit(root.turn, { ended: Date.now() });
        root.turn = -1;
    }

    function elapsed(entry) {
        const until = entry.ended > 0 ? entry.ended : root.now;
        const s = Math.max(0, Math.round((until - entry.started) / 1000));
        return s < 60 ? s + "s" : Math.floor(s / 60) + "m " + (s % 60) + "s";
    }

    Timer {
        interval: 1000
        repeat: true
        running: Agent.busy
        onTriggered: root.now = Date.now()
    }

    // Everything the agent says arrives as a signal, in the order it happened.
    // The pane does not ask for anything — it only writes down what it is told.
    Connections {
        target: Agent

        function onSaid(text) { root.say(text); }

        function onTurnEnded(cost, error) {
            if (error.length > 0)
                root.say("— " + error);
            root.finish();
        }

        function onFailed(why) {
            root.say(why);
            root.finish();
        }
    }

    ScrollView {
        id: scroll
        anchors { left: parent.left; right: parent.right; top: parent.top; bottom: composer.top }
        clip: true

        Column {
            width: root.width
            spacing: 20
            // The newest line is the one being read: keep the bottom in view.
            onHeightChanged: scroll.contentItem.contentY = Math.max(0, height - scroll.height)
            topPadding: 12
            bottomPadding: 8
            leftPadding: 16
            rightPadding: 16

            Repeater {
                model: root.log

                // The question sits on the right in a soft pill; the answer is
                // bare text on the left, the way Palmier Pro draws its chat —
                // where each side is on the page says who spoke, so no badge
                // and no frame has to.
                Item {
                    id: msg
                    required property var modelData
                    readonly property bool mine: msg.modelData.who === "me"
                    readonly property real avail: root.width - 32
                    width: avail
                    height: mine ? pill.height : answer.implicitHeight

                    Rectangle {
                        id: pill
                        visible: msg.mine
                        anchors.right: parent.right
                        width: Math.min(mineText.implicitWidth + 28, msg.avail - 48)
                        height: mineText.implicitHeight + 16
                        radius: 14
                        color: Qt.alpha(Theme.ink, 0.08)

                        Text {
                            id: mineText
                            x: 14
                            y: 8
                            width: parent.width - 28
                            text: msg.mine ? msg.modelData.body.map(b => b.text).join("\n") : ""
                            color: Theme.ink
                            font.family: Theme.ui
                            font.pixelSize: 12
                            lineHeight: 1.4
                            wrapMode: Text.WordWrap
                        }
                    }

                    Column {
                        id: answer
                        visible: !msg.mine
                        width: parent.width
                        spacing: 10

                        Repeater {
                            model: msg.mine ? [] : msg.modelData.body

                            // The agent answers in Markdown.
                            Text {
                                required property var modelData
                                width: answer.width
                                text: modelData.text
                                textFormat: Text.MarkdownText
                                color: Theme.ink
                                font.family: Theme.ui
                                font.pixelSize: 12
                                lineHeight: 1.4
                                wrapMode: Text.WordWrap
                            }
                        }

                        // Three dots breathing in turn while it works; the time
                        // it took, faint, once it is done.
                        Row {
                            id: dots
                            visible: msg.modelData.started > 0 && msg.modelData.ended === 0
                            spacing: 5
                            property int phase: 0
                            Timer {
                                interval: 280
                                repeat: true
                                running: dots.visible && !Theme.reducedMotion
                                onTriggered: dots.phase = (dots.phase + 1) % 3
                            }
                            Repeater {
                                model: 3
                                Rectangle {
                                    required property int index
                                    width: 5; height: 5; radius: 2.5
                                    color: Theme.inkDim
                                    opacity: dots.phase === index ? 1 : 0.25
                                    Behavior on opacity { NumberAnimation { duration: 250 } }
                                }
                            }
                        }

                        Text {
                            visible: msg.modelData.ended > 0
                            text: msg.modelData.ended > 0 ? root.elapsed(msg.modelData) : ""
                            color: Theme.inkFaint
                            font.family: Theme.mono
                            font.pixelSize: 10
                        }
                    }
                }
            }
        }
    }

    // Clicking anywhere in the column means "I want to talk": the caret lands
    // in the field without aiming at the field.
    //
    // Over the content and declining the press it just saw — the same shape as
    // Panel.qml's `floor`, and for the same reason. A TapHandler here was tried
    // first and never fired over the empty transcript: the pane's own floor
    // takes the press, and the ScrollView's Flickable takes the grab, so no tap
    // is ever recognised. Declining the press instead leaves the scroll, the
    // links and the field itself working exactly as before.
    MouseArea {
        anchors.fill: parent
        z: 50
        acceptedButtons: Qt.LeftButton
        cursorShape: undefined // it hands the press back; the cursor is not its to say either
        onPressed: (mouse) => {
            input.forceActiveFocus();
            mouse.accepted = false;
        }
    }

    // No rule between what you read and what you write: one conversation, and
    // the field's own rounded edge already says "type here".
    Item {
        id: composer
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 84

        Rectangle {
            id: box
            anchors.fill: parent
            anchors.margins: 10
            anchors.topMargin: 4
            radius: 20
            color: Theme.rail
            border.width: 1
            border.color: input.activeFocus ? Qt.alpha(Theme.live, 0.55) : Theme.edge

            TextField {
                id: input
                anchors { left: parent.left; right: parent.right; top: parent.top }
                height: 36
                leftPadding: 14
                rightPadding: 14
                topPadding: 10
                placeholderText: Agent.busy ? "Working…" : "Ask for an edit…"
                placeholderTextColor: Theme.inkFaint
                color: Theme.ink
                font.family: Theme.ui
                font.pixelSize: 12
                background: null
                enabled: !Agent.busy
                onAccepted: root.ask(text)
            }

            // Send, as a round button; stop while it works.
            Rectangle {
                id: send
                anchors { right: parent.right; bottom: parent.bottom; margins: 7 }
                width: 24; height: 24; radius: 12
                readonly property bool canSend: !Agent.busy && input.text.length > 0
                color: Agent.busy ? Qt.alpha(Theme.ink, 0.12) : Theme.ai
                opacity: Agent.busy || canSend ? 1 : 0.45

                Text {
                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: Agent.busy ? 0 : -0.5
                    text: Agent.busy ? "■" : "↑"
                    color: Agent.busy ? Theme.ink : Theme.ground
                    font.family: Theme.ui
                    font.pixelSize: Agent.busy ? 9 : 13
                    font.weight: Font.Bold
                }

                HoverTint {}

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: Agent.busy ? Agent.interrupt() : root.ask(input.text)
                }
            }
        }
    }

    function ask(text) {
        if (text.length === 0 || Agent.busy)
            return;
        root.append({ who: "me", body: [{ kind: "text", text: text }] });
        // The answer's block opens before a word of it: with the tools
        // hidden, its dots are what say the agent is working.
        root.now = Date.now();
        root.append({ who: "agent", body: [], started: root.now, ended: 0 });
        root.turn = root.log.length - 1;
        // The shell asks, not the pane: it prefixes what the author is
        // looking at, and only it knows.
        root.sent(text);
        input.text = "";
    }
}
