// The mouse's way out of a popup.
//
// Every overlay in this chrome already answers Escape, and every one of them
// said so in small type beside the title — which is a keyboard instruction on a
// surface you arrived at with a mouse. The word stays; this is the thing you
// can click.
import QtQuick

Rectangle {
    id: root

    signal triggered()

    width: 22
    height: 22
    radius: Theme.radiusSmall
    color: hover.hovered ? Theme.rail : "transparent"
    border.width: 1
    border.color: hover.hovered ? Theme.edge : "transparent"

    Text {
        anchors.centerIn: parent
        text: "✕"
        color: hover.hovered ? Theme.ink : Theme.inkFaint
        font.family: Theme.ui
        font.pixelSize: 11
    }

    HoverHandler {
        id: hover
        cursorShape: Qt.PointingHandCursor
    }

    TapHandler { onTapped: root.triggered() }
}
