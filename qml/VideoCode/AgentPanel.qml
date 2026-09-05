// The conversation, in the right-hand column.
//
// It sits in the dock rather than in a drawer because talking to the agent is not
// an interruption of editing — it IS editing here: what it answers with is code,
// and the code is the scene. So it gets a permanent column, and what used to live
// on the right (Properties, Effects) moves to the element you click.
//
// Every reply shows its work: the tool it ran, the output it read, what it found.
// An agent that edits your scene without showing the call it made is an agent you
// cannot check.
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

    function append(entry) {
        const grown = root.log.slice();
        grown.push(entry);
        root.log = grown;
    }

    // A tool answering lands on the row that ASKED — found by id, never by
    // being the most recent open one. Calls go out in parallel and come back in
    // whichever order they finish: measured, two `Read`s returned with the
    // failing one first, which would have pinned the error to the wrong file.
    function close(id, out, failed) {
        const grown = root.log.slice();
        for (let i = grown.length - 1; i >= 0; i--) {
            const body = grown[i].body;
            for (let j = 0; j < body.length; j++) {
                if (body[j].kind !== "tool" || body[j].id !== id)
                    continue;
                const rebuilt = body.slice();
                rebuilt[j] = {
                    kind: "tool", id: id, call: body[j].call,
                    out: out, failed: failed, findings: []
                };
                grown[i] = { who: grown[i].who, body: rebuilt };
                root.log = grown;
                return;
            }
        }
    }

    // Everything the agent says arrives as a signal, in the order it happened.
    // The pane does not ask for anything — it only writes down what it is told.
    Connections {
        target: Agent

        function onSaid(text) { root.append({ who: "agent", body: [{ kind: "text", text: text }] }); }

        function onToolStarted(id, name, summary) {
            root.append({ who: "agent",
                          body: [{ kind: "tool", id: id, call: name + "(" + summary + ")" }] });
        }

        function onToolEnded(id, name, output, failed) { root.close(id, output, failed); }

        function onTurnEnded(cost, error) {
            if (error.length > 0)
                root.append({ who: "agent", body: [{ kind: "text", text: "— " + error }] });
        }

        function onFailed(why) { root.append({ who: "agent", body: [{ kind: "text", text: why }] }); }
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

                Row {
                    id: msg
                    required property var modelData
                    width: root.width - 24
                    spacing: 9

                    Rectangle {
                        width: 21; height: 21
                        radius: 4
                        color: msg.modelData.who === "me" ? Theme.rail : Qt.rgba(0.416, 0.651, 0.878, 0.133)
                        border.width: 1
                        border.color: msg.modelData.who === "me" ? Theme.edge : Qt.rgba(0.416, 0.651, 0.878, 0.333)

                        Text {
                            anchors.centerIn: parent
                            text: msg.modelData.who === "me" ? "MR" : "AI"
                            color: msg.modelData.who === "me" ? Theme.inkDim : Theme.ai
                            font.family: Theme.mono
                            font.pixelSize: 9
                            font.weight: Font.Bold
                        }
                    }

                    Column {
                        width: parent.width - 30
                        spacing: 6

                        Text {
                            text: msg.modelData.who === "me" ? "ME" : "AGENT"
                            color: Theme.inkFaint
                            font.family: Theme.ui
                            font.pixelSize: 10
                            font.letterSpacing: 0.8
                        }

                        Repeater {
                            model: msg.modelData.body

                            Column {
                                id: block
                                required property var modelData
                                width: parent.width
                                spacing: 0

                                Text {
                                    visible: block.modelData.kind === "text"
                                    width: parent.width
                                    text: block.modelData.kind === "text" ? block.modelData.text : ""
                                    color: Theme.ink
                                    font.family: Theme.ui
                                    font.pixelSize: 12
                                    lineHeight: 1.4
                                    wrapMode: Text.WordWrap
                                }

                                // The call, its output, and what it found — the
                                // three things you need to trust the answer.
                                Rectangle {
                                    visible: block.modelData.kind === "tool"
                                    width: parent.width
                                    height: visible ? toolBody.implicitHeight + 2 : 0
                                    radius: Theme.radius
                                    color: Theme.sunk
                                    border.color: Theme.edge
                                    border.width: 1

                                    Column {
                                        id: toolBody
                                        width: parent.width - 2
                                        x: 1
                                        y: 1

                                        Rectangle {
                                            width: parent.width
                                            height: 24
                                            color: Theme.rail
                                            topLeftRadius: Theme.radius - 1
                                            topRightRadius: Theme.radius - 1

                                            Row {
                                                anchors.verticalCenter: parent.verticalCenter
                                                anchors.left: parent.left
                                                anchors.leftMargin: 9
                                                spacing: 7

                                                Text {
                                                    text: "✓"
                                                    color: Theme.ok
                                                    font.pixelSize: 11
                                                }

                                                Text {
                                                    text: block.modelData.kind === "tool" ? block.modelData.call : ""
                                                    color: Theme.inkDim
                                                    font.family: Theme.mono
                                                    font.pixelSize: 11
                                                }
                                            }

                                            Rectangle {
                                                anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                                                height: 1
                                                color: Theme.edge
                                            }
                                        }

                                        Text {
                                            width: parent.width
                                            leftPadding: 9; rightPadding: 9
                                            topPadding: 6; bottomPadding: 6
                                            text: block.modelData.kind === "tool" ? block.modelData.out : ""
                                            color: Theme.inkDim
                                            font.family: Theme.mono
                                            font.pixelSize: 11
                                            wrapMode: Text.Wrap
                                        }

                                        Repeater {
                                            model: block.modelData.kind === "tool" ? block.modelData.findings : []

                                            Item {
                                                id: finding
                                                required property var modelData
                                                width: toolBody.width
                                                height: 20

                                                Text {
                                                    anchors.left: parent.left
                                                    anchors.leftMargin: 9
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    text: finding.modelData.range
                                                    color: Theme.live
                                                    font.family: Theme.mono
                                                    font.pixelSize: 10
                                                }

                                                Text {
                                                    anchors.right: parent.right
                                                    anchors.rightMargin: 9
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    text: finding.modelData.dur
                                                    color: Theme.inkFaint
                                                    font.family: Theme.mono
                                                    font.pixelSize: 10
                                                }
                                            }
                                        }

                                        Item { width: 1; height: 4 }
                                    }
                                }
                            }
                        }
                    }
                }
            }
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
                // The shell asks, not the pane: it prefixes what the author is
                // looking at, and only it knows.
                root.sent(text);
                text = "";
            }
        }
    }
}
