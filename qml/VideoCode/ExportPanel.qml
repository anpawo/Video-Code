// The render, while it is happening.
//
// The editor could not make a file at all until now: the scene was written
// here and rendered somewhere else, in a terminal, by hand. So the one thing
// this panel owes the author is the truth about a job that takes minutes —
// what it is writing, which stretch of the scene, how far it has got, and how
// it ended. A spinner that says nothing would be worse than the terminal it
// replaces, where at least the frames counted up.
//
// The count is the renderer's own, read off the line it already prints. This
// panel invents no number of its own: one that could disagree with the file
// being written is exactly the kind of comfort this project refuses.
pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: root
    anchors.fill: parent
    visible: false

    // Where it is being written, and the stretch being rendered — "" and -1
    // for the whole scene.
    property string target: ""
    property real from: -1
    property real to: -1

    property int done: 0
    property int total: 0

    // running · ok · failed
    property string state: "running"
    property string message: ""

    signal cancelled()

    readonly property real fraction: root.total > 0 ? root.done / root.total : 0

    function begin(where, first, last) {
        root.target = where;
        root.from = first;
        root.to = last;
        root.done = 0;
        root.total = 0;
        root.state = "running";
        root.message = "";
        root.visible = true;
        root.forceActiveFocus();
    }

    function advance(written, all) {
        root.done = written;
        root.total = all;
    }

    function settle(ok, said) {
        root.state = ok ? "ok" : "failed";
        root.message = said;
        if (ok && root.total > 0)
            root.done = root.total;
    }

    function stop() {
        if (root.state === "running")
            root.cancelled();
        else
            root.visible = false;
    }

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.55)

        MouseArea {
            anchors.fill: parent
            // A click outside closes a finished export and leaves a running one
            // alone: the second is a job, and jobs are not dismissed by
            // accident.
            onClicked: if (root.state !== "running") root.visible = false
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: Math.min(480, root.width - 80)
        height: body.implicitHeight + 44
        color: Theme.panel
        radius: Theme.radius
        border.width: 1
        border.color: Theme.edge

        MouseArea { anchors.fill: parent }

        Column {
            id: body
            anchors { left: parent.left; right: parent.right; top: parent.top; topMargin: 18 }
            spacing: 10

            Text {
                leftPadding: 18
                text: root.state === "failed" ? "Export failed" : "Export"
                color: root.state === "failed" ? Theme.warn : Theme.ink
                font.family: Theme.ui
                font.pixelSize: 13
                font.weight: Font.DemiBold
            }

            Text {
                leftPadding: 18
                rightPadding: 18
                width: body.width
                text: root.target.split("/").pop()
                color: Theme.inkDim
                font.family: Theme.mono
                font.pixelSize: 11
                elide: Text.ElideMiddle
            }

            Text {
                leftPadding: 18
                text: root.from >= 0 && root.to > root.from
                      ? "the range you marked — " + root.from.toFixed(2) + "s to " + root.to.toFixed(2) + "s"
                      : "the whole scene"
                color: Theme.inkFaint
                font.family: Theme.ui
                font.pixelSize: 10
            }

            // ── How far ──────────────────────────────────────────────────
            Item {
                width: body.width
                height: 8

                Rectangle {
                    anchors { left: parent.left; leftMargin: 18; right: parent.right; rightMargin: 18
                              verticalCenter: parent.verticalCenter }
                    height: 6
                    radius: 3
                    color: Theme.sunk

                    Rectangle {
                        width: Math.max(parent.width * root.fraction, root.fraction > 0 ? 3 : 0)
                        height: parent.height
                        radius: parent.radius
                        color: root.state === "failed" ? Theme.warn
                             : root.state === "ok" ? Theme.ok : Theme.live
                        Behavior on width { NumberAnimation { duration: 120 } }
                    }
                }
            }

            Text {
                leftPadding: 18
                text: root.state === "ok" ? "✓  " + root.message
                    : root.state === "failed" ? root.message
                    : root.total > 0
                      ? root.done + " of " + root.total + " frames  ·  " + Math.round(root.fraction * 100) + "%"
                      : "starting the renderer…"
                color: root.state === "failed" ? Theme.warn
                     : root.state === "ok" ? Theme.ok : Theme.inkDim
                font.family: Theme.mono
                font.pixelSize: 10
            }

            Item {
                width: body.width
                height: 26

                Rectangle {
                    anchors { right: parent.right; rightMargin: 18; verticalCenter: parent.verticalCenter }
                    width: word.implicitWidth + 22
                    height: 24
                    radius: Theme.radiusSmall
                    color: hit.containsMouse ? Theme.rail : "transparent"
                    border.width: 1
                    border.color: Theme.edge

                    Text {
                        id: word
                        anchors.centerIn: parent
                        text: root.state === "running" ? "Stop" : "Close"
                        color: Theme.ink
                        font.family: Theme.ui
                        font.pixelSize: 11
                    }

                    MouseArea {
                        id: hit
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.stop()
                    }
                }
            }
        }
    }

    Keys.onEscapePressed: root.stop()
}
