// The picture, plus the transport that moves through it.
//
// The picture is real: `PreviewItem` asks the shell to render the current frame
// with the same engine `--generate` uses, headless into an offscreen image, and
// hands it to the scene graph as a texture. Not the old `VulkanWidget` path —
// that paints onto a native surface with WA_PaintOnScreen, which Qt Quick cannot
// composite over; two devices in one process turned out to be cheaper than
// making one device serve two masters.
//
// It renders at PANE size, not at output size: 4x SSAA makes a 1080p frame a
// 7680x4320 offscreen buffer, and this is a viewport, not a deliverable. What
// you see is the scene; what you see is not the file.
import QtQuick

import VideoCode.Engine

Item {
    id: root

    property real playhead: 0
    property int frameWidth: 1920
    property int frameHeight: 1080
    property int framerate: 30
    property bool playing: false

    // Which scene: bumped on every successful execute, so the same frame index
    // is re-rendered when the buffer behind it has changed.
    property int revision: 0

    // Whether there is a scene at all. Before the first ⌘R there is nothing to
    // draw, and drawing nothing is better than drawing the last thing.
    property bool ready: false

    signal togglePlay()

    // The button in the transport bar: make a file of this.
    signal exportAsked()
    signal seek(real seconds)

    // Clicking the picture is working in the picture: the caret leaves the code
    // pane, and the transport keys — Space, the arrows, Home, End — come back
    // from the text editor that owns them while you are typing.
    MouseArea {
        anchors.fill: parent
        onPressed: root.forceActiveFocus()
    }

    // ── Stage: the frame is letterboxed inside whatever room the dock gives ──
    Item {
        id: stage
        anchors {
            left: parent.left; right: parent.right
            top: parent.top; bottom: viewbar.top
            // Tight, because the pane is sized to the picture rather than the
            // picture floated in whatever pane was left over.
            margins: 5
        }

        Rectangle {
            id: frame
            anchors.centerIn: parent
            readonly property real aspect: root.frameWidth / root.frameHeight
            width: Math.min(parent.width, parent.height * aspect)
            height: width / aspect
            color: Theme.sunk
            border.color: Theme.edge
            border.width: 1

            PreviewItem {
                id: picture
                anchors.fill: parent
                anchors.margins: 1
                visible: root.ready
                shell: Shell
                revision: root.revision
                // The playhead is in seconds because that is what a person
                // reads; a renderer only knows frames.
                frame: Math.round(root.playhead * root.framerate)
            }

            Text {
                anchors.centerIn: parent
                visible: !root.ready
                text: "⌘R to run the scene"
                color: Theme.inkFaint
                font.family: Theme.mono
                font.pixelSize: 11
            }
        }
    }

    // ── Viewbar ───────────────────────────────────────────────────────────
    Rectangle {
        id: viewbar
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 30
        color: Theme.rail
        // The viewbar is the panel's bottom edge, so it carries the panel's
        // corners; left square, it paints over them.
        bottomLeftRadius: Theme.radiusInner
        bottomRightRadius: Theme.radiusInner

        Rectangle {
            anchors { left: parent.left; right: parent.right; top: parent.top }
            height: 1
            color: Theme.edge
        }

        Row {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 8
            spacing: 2

            TransportButton { glyph: "⏮"; onTriggered: { root.forceActiveFocus(); root.seek(0); } }
            TransportButton { glyph: "◀"; onTriggered: root.seek(root.playhead - 1 / root.framerate) }
            TransportButton {
                glyph: root.playing ? "❙❙" : "▶"
                active: root.playing
                onTriggered: { root.forceActiveFocus(); root.togglePlay(); }
            }
            TransportButton { glyph: "▶"; onTriggered: root.seek(root.playhead + 1 / root.framerate) }
        }

        // Timecode counts frames, because a video editor's smallest unit is a
        // frame — not a tenth of a second.
        Text {
            anchors.centerIn: parent
            color: Theme.ink
            font.family: Theme.mono
            font.pixelSize: 12
            text: {
                const total = Math.floor(root.playhead);
                const h = String(Math.floor(total / 3600)).padStart(2, "0");
                const m = String(Math.floor(total / 60) % 60).padStart(2, "0");
                const s = String(total % 60).padStart(2, "0");
                const f = String(Math.round((root.playhead - total) * root.framerate)).padStart(2, "0");
                return h + ":" + m + ":" + s + ":" + f;
            }
        }

        // Beside the size and the frame rate, because that is what the button
        // makes a file of — and it is the one thing the editor could not do at
        // all until now.
        Rectangle {
            id: exportButton
            anchors { verticalCenter: parent.verticalCenter; right: parent.right; rightMargin: 10 }
            width: exportWord.implicitWidth + 18
            height: 22
            radius: Theme.radiusSmall
            color: exportHit.containsMouse ? Theme.rail : "transparent"
            border.width: 1
            border.color: exportHit.containsMouse ? Theme.edge : Theme.edgeSoft

            Text {
                id: exportWord
                anchors.centerIn: parent
                text: "Export"
                color: Theme.inkDim
                font.family: Theme.ui
                font.pixelSize: 10
            }

            MouseArea {
                id: exportHit
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.exportAsked()
            }
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: exportButton.left
            anchors.rightMargin: 12
            text: root.frameWidth + "×" + root.frameHeight + "  ·  " + root.framerate + " fps"
            color: Theme.inkFaint
            font.family: Theme.mono
            font.pixelSize: 10
        }
    }
}
