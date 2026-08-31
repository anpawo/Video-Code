// One line of facts about the running scene. Nothing here is a control: the
// status strip reports, it does not offer.
import QtQuick

Rectangle {
    id: root

    property int compileMs: 0
    property real frameMs: 0
    property int inputCount: 0
    property bool live: true

    // What the last ⌘R did, and whether the buffer has moved since.
    //
    // The strip carries it because this is the one line that is always on
    // screen whatever the arrangement — and because a picture that is behind
    // the buffer has to SAY so. `guideColors()` already promises that warn
    // means "stale — the picture is behind the buffer"; this is what keeps
    // that promise.
    property string execState: "none"
    property bool execStale: false
    property real execMs: 0

    height: Theme.statusHeight
    color: Theme.rail

    Rectangle {
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: 1
        color: Theme.edge
    }

    Row {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: 10
        spacing: 14

        Row {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 5

            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: 6; height: 6; radius: 3
                color: root.live ? Theme.ok : Theme.inkFaint
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: "hot-reload"
                color: Theme.inkFaint
                font.family: Theme.mono
                font.pixelSize: 10
            }
        }

        Row {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 5
            visible: root.execState !== "none"

            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: 6; height: 6; radius: 3
                color: root.execState === "failed"
                       ? Theme.bad
                       : (root.execStale ? Theme.warn : Theme.ok)
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: root.execState === "failed"
                      ? "scene failed — ⌘R"
                      : (root.execStale
                         ? "stale — ⌘R"
                         : "ran " + root.execMs.toFixed(0) + " ms")
                color: root.execState === "failed"
                       ? Theme.bad
                       : (root.execStale ? Theme.warn : Theme.inkFaint)
                font.family: Theme.mono
                font.pixelSize: 10
            }
        }

        Text {
            text: "compiled " + root.compileMs + " ms"
            color: Theme.inkFaint
            font.family: Theme.mono
            font.pixelSize: 10
        }

        Text {
            text: root.inputCount + " inputs"
            color: Theme.inkFaint
            font.family: Theme.mono
            font.pixelSize: 10
        }
    }

    Text {
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: 10
        text: root.frameMs.toFixed(1) + " ms/frame"
        color: Theme.inkFaint
        font.family: Theme.mono
        font.pixelSize: 10
    }
}
