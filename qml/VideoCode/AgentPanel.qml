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
        anchors { left: parent.left; right: parent.right; top: parent.top; bottom: composer.top }
        clip: true

        Column {
            width: root.width
            spacing: 14
            padding: 12

            Repeater {
                model: root.log

                // The question and the answer in two soft tints: down a long
                // column, where one exchange ends and the next begins is what the
                // eye looks for first.
                Rectangle {
                    id: msg
                    required property var modelData
                    readonly property color tint: msg.modelData.who === "me" ? Theme.inkDim : Theme.ai
                    width: root.width - 24
                    height: row.implicitHeight + 20
                    radius: Theme.radius
                    color: Qt.alpha(msg.tint, 0.08)
                    border.width: 1
                    border.color: Qt.alpha(msg.tint, 0.22)

                    Row {
                        id: row
                        x: 10
                        y: 10
                        width: parent.width - 20
                        spacing: 9

                        Rectangle {
                            width: 21; height: 21
                            radius: 4
                            color: msg.modelData.who === "me" ? Theme.rail : Qt.rgba(0.416, 0.651, 0.878, 0.133)
                            border.width: 1
                            border.color: msg.modelData.who === "me" ? Theme.edge : Qt.rgba(0.416, 0.651, 0.878, 0.333)

                            Text {
                                anchors.centerIn: parent
                                text: msg.modelData.who === "me" ? "ME" : "AI"
                                color: msg.modelData.who === "me" ? Theme.inkDim : Theme.ai
                                font.family: Theme.mono
                                font.pixelSize: 9
                                font.weight: Font.Bold
                            }
                        }

                        Column {
                            id: lines
                            width: parent.width - 30
                            // Level with the badge on one line; a taller answer runs down from its top.
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 6

                            Row {
                                visible: msg.modelData.started > 0
                                spacing: 8

                                // A Canvas, not QtQuick.Shapes: see KeyGlyph.qml.
                                Canvas {
                                    id: spinner
                                    width: 10
                                    height: 10
                                    anchors.verticalCenter: parent.verticalCenter
                                    antialiasing: true
                                    visible: msg.modelData.started > 0 && msg.modelData.ended === 0
                                    onPaint: {
                                        const ctx = getContext("2d");
                                        ctx.reset();
                                        ctx.strokeStyle = Theme.ai;
                                        ctx.lineWidth = 1.5;
                                        ctx.lineCap = "round";
                                        ctx.beginPath();
                                        ctx.arc(5, 5, 3.75, 0, Math.PI * 1.5);
                                        ctx.stroke();
                                    }

                                    RotationAnimator on rotation {
                                        from: 0
                                        to: 360
                                        duration: 900
                                        loops: Animation.Infinite
                                        running: spinner.visible && !Theme.reducedMotion
                                    }
                                }

                                // Blue while the agent works, faint once it is done.
                                Text {
                                    text: msg.modelData.started > 0 ? root.elapsed(msg.modelData) : ""
                                    color: msg.modelData.ended > 0 ? Theme.inkFaint : Theme.ai
                                    font.family: Theme.mono
                                    font.pixelSize: 10
                                }
                            }

                            Repeater {
                                model: msg.modelData.body

                                Column {
                                    id: block
                                    required property var modelData
                                    // Not `parent.width`: a delegate has no parent yet
                                    // when its bindings first run.
                                    width: lines.width
                                    spacing: 0

                                    // The agent answers in Markdown; what the author
                                    // typed is shown as typed.
                                    Text {
                                        visible: block.modelData.kind === "text"
                                        width: parent.width
                                        text: block.modelData.kind === "text" ? block.modelData.text : ""
                                        textFormat: msg.modelData.who === "agent" ? Text.MarkdownText : Text.PlainText
                                        color: Theme.ink
                                        font.family: Theme.ui
                                        font.pixelSize: 12
                                        lineHeight: 1.4
                                        wrapMode: Text.WordWrap
                                    }
                                }
                            }
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
        onPressed: (mouse) => {
            input.forceActiveFocus();
            mouse.accepted = false;
        }
    }

    // No rule between what you read and what you write. A line there says the two
    // are separate places; they are one conversation, and the field's own border
    // is already enough to say "type here" — which is how every chat worth using
    // draws it.
    Rectangle {
        id: composer
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 44
        color: "transparent"

        TextField {
            id: input
            anchors.fill: parent
            anchors.margins: 8
            placeholderText: Agent.busy ? "Working…" : "Ask for an edit…"
            color: Theme.ink
            font.family: Theme.ui
            font.pixelSize: 12
            background: Rectangle {
                color: Theme.sunk
                radius: Theme.radiusSmall
                border.width: 1
                border.color: input.activeFocus ? Theme.live : Theme.edge
            }
            enabled: !Agent.busy
            onAccepted: {
                if (text.length === 0)
                    return;
                root.append({ who: "me", body: [{ kind: "text", text: text }] });
                // The answer's block opens before a word of it: with the tools
                // hidden, its counter is what says the agent is working.
                root.now = Date.now();
                root.append({ who: "agent", body: [], started: root.now, ended: 0 });
                root.turn = root.log.length - 1;
                // The shell asks, not the pane: it prefixes what the author is
                // looking at, and only it knows.
                root.sent(text);
                text = "";
            }
        }
    }
}
