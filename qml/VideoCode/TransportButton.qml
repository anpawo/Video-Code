// A transport key: flat until you point at it, accented while it is the state
// you are in. Small enough that a Controls Button would only get in the way.
import QtQuick

Rectangle {
    id: root

    property string glyph: ""
    property bool active: false

    signal triggered()

    width: 24; height: 20
    radius: Theme.radiusSmall
    color: root.active ? Theme.liveSoft
                       : (hover.hovered ? Theme.panel : "transparent")

    Text {
        anchors.centerIn: parent
        text: root.glyph
        color: root.active ? Theme.live : Theme.inkDim
        font.pixelSize: 10
    }

    HoverHandler { id: hover }

    TapHandler { onTapped: root.triggered() }
}
