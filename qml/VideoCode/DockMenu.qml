// The slot menu: what exists, and what to do with the dock.
//
// Drawn by the shell at the window's top level rather than inside the slot that
// asked for it. A menu is bigger than the strip it hangs from and would be
// covered by the neighbouring pane — or clipped by its own panel — anywhere else.
//
// Entries are objects, and the chosen one comes back whole rather than as an
// index into a list the caller has to remember: a submenu makes an index a
// coordinate pair, and a coordinate pair is a bug waiting for its second level.
pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: root

    // [{ kind, label, … }] where kind is "item", "check", "rule" or "sub".
    // A "sub" entry carries its own list in `sub`.
    property var entries: []

    signal chosen(var entry)

    visible: false

    property int openSub: -1

    function popup(x, y) {
        openSub = -1;
        sheet.x = Math.max(4, Math.min(x, root.width - sheet.width - 4));
        sheet.y = Math.max(4, Math.min(y, root.height - sheet.height - 4));
        visible = true;
    }

    // Anywhere else is "no thanks". A menu you have to aim at to dismiss is a
    // menu that has taken the window hostage.
    MouseArea {
        anchors.fill: parent
        onPressed: root.visible = false
    }

    component Sheet: Rectangle {
        id: sheetBody

        property var rows: []
        property bool nested: false

        width: 208
        height: column.height + 8
        color: Theme.panel
        border.color: Theme.edge
        border.width: 1
        radius: Theme.radiusSmall

        Column {
            id: column
            y: 4
            width: parent.width

            Repeater {
                model: sheetBody.rows

                Item {
                    id: line
                    required property int index
                    required property var modelData
                    width: sheetBody.width
                    height: line.modelData.kind === "rule" ? 7 : 24

                    readonly property bool openable: line.modelData.kind === "sub"
                    readonly property bool pickable: line.modelData.kind !== "rule"

                    Rectangle {
                        visible: line.modelData.kind === "rule"
                        anchors.centerIn: parent
                        width: parent.width - 16
                        height: 1
                        color: Theme.edgeSoft
                    }

                    Rectangle {
                        visible: line.pickable
                        anchors.fill: parent
                        anchors.leftMargin: 4
                        anchors.rightMargin: 4
                        radius: Theme.radiusSmall
                        color: hover.hovered || (line.openable && root.openSub === line.index && !sheetBody.nested)
                               ? Theme.rail : "transparent"

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 10
                            text: line.modelData.kind === "check"
                                  ? (line.modelData.on ? "✓  " : "     ") + line.modelData.label
                                  : line.modelData.label
                            color: hover.hovered ? Theme.ink : Theme.inkDim
                            font.family: Theme.ui
                            font.pixelSize: 12
                        }

                        // The one affordance a submenu owes you: that there is
                        // more behind it.
                        Text {
                            visible: line.openable
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.right: parent.right
                            anchors.rightMargin: 9
                            text: "›"
                            color: Theme.inkFaint
                            font.pixelSize: 13
                        }
                    }

                    HoverHandler {
                        id: hover
                        enabled: line.pickable
                        // Pointing at anything closes whatever else was open, so
                        // two submenus can never be on screen at once.
                        onHoveredChanged: {
                            if (!hovered || sheetBody.nested)
                                return;
                            root.openSub = line.openable ? line.index : -1;
                            if (line.openable) {
                                nest.rows = line.modelData.sub;
                                nest.x = sheet.x + sheet.width - 6;
                                nest.y = sheet.y + line.y + 4;
                            }
                        }
                    }

                    TapHandler {
                        enabled: line.pickable
                        onTapped: {
                            // A submenu opens on hover, but must open on a click
                            // too: pointing is not the only way people drive a
                            // menu, and a row that swallows clicks reads as dead.
                            if (line.openable) {
                                root.openSub = root.openSub === line.index ? -1 : line.index;
                                nest.rows = line.modelData.sub;
                                nest.x = sheet.x + sheet.width - 6;
                                nest.y = sheet.y + line.y + 4;
                                return;
                            }
                            root.visible = false;
                            root.chosen(line.modelData);
                        }
                    }
                }
            }
        }
    }

    Sheet {
        id: sheet
        rows: root.entries
    }

    Sheet {
        id: nest
        nested: true
        visible: root.openSub >= 0
    }
}
