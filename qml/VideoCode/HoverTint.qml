// The pointer's answer, for anything that takes a click or a drag and had
// none: dropped into the item, it lays the one hover veil over it. Over, not
// under — a child below its parent is hidden by the parent's own fill — and at
// five per cent the text under it still reads. A HoverHandler, so the presses
// still go to whatever already takes them.
import QtQuick

Rectangle {
    anchors.fill: parent
    radius: (parent as Rectangle)?.radius ?? 0
    color: hover.hovered ? Theme.hover : "transparent"

    HoverHandler { id: hover }
}
