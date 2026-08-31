// The bin, in one of two shapes.
//
// GRID is the default: what you reach for here you recognise by its picture, and
// a filename alone makes every asset look the same.
//
// DETAILS is for when the column is narrow or the names matter more than the
// pictures — writing the scene by hand, where you are looking for the exact
// spelling of a filename to type, not for a thumbnail. It is the shape the Code
// template opens with, and either shape can be chosen from the slot's ⋯ menu.
//
// A full-height column on the far left in every layout — it is the one thing you
// reach for regardless of what you are doing, and a browser that changes place
// between layouts costs you the muscle memory of finding it.
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls

Item {
    id: root

    required property var sceneAssets

    // Files added from the panel itself, shown after the scene's own.
    property var added: []

    readonly property var assets: sceneAssets.concat(added)

    // "grid" or "list".
    property string display: "grid"

    signal assetPicked(string name)
    signal addRequested()

    // Carried out of the bin and over the window. A file is not placed by being
    // clicked — it is placed at a MOMENT, and the only surface that knows about
    // moments is the timeline. So the bin says what is under the hand and where
    // the hand is, and lets whatever is under it decide.
    signal assetCarried(var asset, real globalX, real globalY)
    signal assetDropped(var asset, real globalX, real globalY)
    signal carryCancelled()

    // How far a press has to travel before it stops being a click. Short: a bin
    // row is small, and a file you meant to drag should not need a run-up.
    readonly property int dragThreshold: 5

    component Carry: MouseArea {
        id: carry
        property var asset: null
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        // The pointer leaves this pane almost immediately — that is the whole
        // gesture — and every surface it crosses has its own grabs. Without
        // this the drag was CANCELLED on the way out and the drop never
        // happened, which looked like the bin refusing to give the file up.
        preventStealing: true

        property bool moving: false
        property real fromX: 0
        property real fromY: 0

        onPressed: (mouse) => {
            const at = mapToGlobal(mouse.x, mouse.y);
            carry.fromX = at.x;
            carry.fromY = at.y;
            carry.moving = false;
        }

        onPositionChanged: (mouse) => {
            if (!pressed)
                return;
            const at = mapToGlobal(mouse.x, mouse.y);
            if (!carry.moving
                && Math.abs(at.x - carry.fromX) < root.dragThreshold
                && Math.abs(at.y - carry.fromY) < root.dragThreshold)
                return;
            carry.moving = true;
            root.assetCarried(carry.asset, at.x, at.y);
        }

        onReleased: (mouse) => {
            const at = mapToGlobal(mouse.x, mouse.y);
            if (carry.moving)
                root.assetDropped(carry.asset, at.x, at.y);
            else
                root.assetPicked(carry.asset.n);
            carry.moving = false;
        }

        onCanceled: {
            carry.moving = false;
            root.carryCancelled();
        }
    }

    // The scene as the window knows it, for the one column a bin can fill
    // honestly: how many times a file is actually in the edit.
    property var scene: ({ elements: [] })

    // `scene` was read here as a global and there is no such global: every card
    // drawn threw a ReferenceError, and the column that answers "is this thing
    // in the cut" answered nothing.
    function timesUsed(name) {
        let count = 0;
        for (const one of (root.scene.elements || []))
            if (one.n === name)
                count++;
        return count;
    }

    ScrollView {
        anchors.fill: parent
        clip: true
        visible: root.display === "grid"

        Flow {
            width: root.width
            padding: 9
            spacing: 7

            Repeater {
                model: root.assets

                Rectangle {
                    id: card
                    required property var modelData
                    // Two columns in the narrow left rail, more if the slot grows.
                    width: Math.max((root.width - 18 - 7) / 2, 80)
                    height: thumb.height + caption.height + 2
                    radius: Theme.radius
                    color: Theme.sunk
                    border.width: 1
                    border.color: cardHover.hovered ? Theme.inkFaint : Theme.edge

                    Rectangle {
                        id: thumb
                        anchors { left: parent.left; right: parent.right; top: parent.top }
                        anchors.margins: 1
                        height: width * 9 / 16
                        color: Qt.alpha(Theme.kind[card.modelData.kind], 0.26)
                        topLeftRadius: Theme.radius - 1
                        topRightRadius: Theme.radius - 1
                        clip: true

                        // A real picture when the file is on disk: the opening
                        // frame of a video, the image itself for a still —
                        // decoded small and rough on purpose, at the size it is
                        // drawn and no more. Anything the decoders cannot read
                        // stays the coloured card underneath, which is answer
                        // enough.
                        Image {
                            id: shot
                            anchors.fill: parent
                            visible: status === Image.Ready
                            asynchronous: true
                            cache: true
                            fillMode: Image.PreserveAspectCrop
                            sourceSize.width: 96
                            source: card.modelData.path !== undefined
                                    ? "image://thumb/" + card.modelData.path : ""
                        }

                        KindGlyph {
                            anchors.centerIn: parent
                            visible: shot.status !== Image.Ready
                            kind: card.modelData.kind
                            tint: Qt.rgba(1.000, 1.000, 1.000, 0.267)
                            size: 16
                        }
                    }

                    Text {
                        id: caption
                        anchors { left: parent.left; right: parent.right; top: thumb.bottom }
                        leftPadding: 6
                        rightPadding: 6
                        topPadding: 4
                        bottomPadding: 5
                        text: card.modelData.n
                        color: Theme.inkDim
                        font.family: Theme.ui
                        font.pixelSize: 11
                        elide: Text.ElideRight
                    }

                    HoverHandler { id: cardHover }
                    Carry { asset: card.modelData }
                }
            }

            // The same offer, in the cell the next card would take.
            Rectangle {
                width: Math.max((root.width - 18 - 7) / 2, 80)
                height: width * 9 / 16 + 8
                radius: Theme.radius
                color: gridAddHover.hovered ? Qt.alpha(Theme.live, 0.08) : "transparent"
                border.width: 1
                border.color: gridAddHover.hovered ? Qt.alpha(Theme.live, 0.45) : Theme.edge

                Text {
                    anchors.centerIn: parent
                    text: "＋"
                    color: gridAddHover.hovered ? Theme.live : Theme.inkFaint
                    font.pixelSize: 16
                }

                HoverHandler { id: gridAddHover }
                TapHandler { onTapped: root.addRequested() }
            }
        }
    }

    // ── Details ───────────────────────────────────────────────────────────
    Item {
        anchors.fill: parent
        visible: root.display === "list"

        Rectangle {
            id: header
            anchors { left: parent.left; right: parent.right; top: parent.top }
            height: 20
            color: Theme.rail

            Text {
                anchors.verticalCenter: parent.verticalCenter
                x: 28
                text: "NAME"
                color: Theme.inkFaint
                font.family: Theme.ui
                font.pixelSize: 9
                font.letterSpacing: 0.6
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.rightMargin: 14
                text: "USED"
                color: Theme.inkFaint
                font.family: Theme.ui
                font.pixelSize: 9
                font.letterSpacing: 0.6
            }

            Rectangle {
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                height: 1
                color: Theme.edge
            }
        }

        ListView {
            id: rows
            anchors {
                left: parent.left; right: parent.right
                top: header.bottom; bottom: parent.bottom
            }
            clip: true
            model: root.assets
            // A hair of air between rows. Touching rows read as one block of
            // colour and the eye stops counting them; two pixels is enough to
            // make each row a thing.
            // The gap between rows belongs to the rows themselves (each is a
            // 24-high frame holding a 22-high tint), not to the view: a ListView
            // places its delegates on BOTH axes, so an x set on one is thrown
            // away — which is what left the rows flush against the left edge
            // while their width was still eight pixels short on the right.
            spacing: 0
            topMargin: 2

            // The offer to add one is the list's footer rather than a box placed
            // after it by hand: the view then owns its width and the gap above
            // it, so it cannot drift out of line with the rows or sit flush
            // against the last one.
            footer: Item {
                width: rows.width
                height: 24

                Rectangle {
                    x: 4
                    y: 1
                    width: rows.width - 8
                    height: 22
                    radius: 3
                    color: addHover.hovered ? Qt.alpha(Theme.live, 0.10) : "transparent"
                    border.width: 1
                    border.color: addHover.hovered ? Qt.alpha(Theme.live, 0.45) : Theme.edge

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        // On the same two columns as a file row: the mark where
                        // the glyphs are, the words where the names are.
                        anchors.leftMargin: 5
                        text: "＋"
                        color: addHover.hovered ? Theme.live : Theme.inkFaint
                        font.family: Theme.ui
                        font.pixelSize: 11
                    }

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        x: 24
                        text: "Add media…"
                        color: addHover.hovered ? Theme.live : Theme.inkFaint
                        font.family: Theme.ui
                        font.pixelSize: 11
                    }

                    HoverHandler { id: addHover }
                    TapHandler { onTapped: root.addRequested() }
                }
            }

            delegate: Item {
                id: line
                required property var modelData
                required property int index
                width: ListView.view.width
                height: 24

                Rectangle {
                id: row
                readonly property var modelData: line.modelData
                x: 4
                y: 1
                width: parent.width - 8
                height: 22
                radius: 3
                // The kind IS the row. A dot in a column is a legend you have to
                // look up; a tinted row is read at a glance and needs no column
                // of its own, which is why there is no KIND column either. The
                // alpha is low enough that the name still reads as ink on the
                // panel rather than as text on a colour.
                color: Qt.alpha(Theme.kind[row.modelData.kind], rowHover.hovered ? 0.34 : 0.16)

                // The same glyph the grid puts on its cards, so the two shapes of
                // this panel are the same panel. The colour says WHICH kind; the
                // glyph says what a kind IS, which is what you need the first
                // time you see a hue you have not learnt yet.
                KindGlyph {
                    anchors.verticalCenter: parent.verticalCenter
                    x: 9
                    kind: row.modelData.kind
                    tint: Theme.kind[row.modelData.kind]
                    size: 11
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    x: 28
                    width: parent.width - 26 - 40
                    text: row.modelData.n
                    color: rowHover.hovered ? Theme.ink : Theme.inkDim
                    font.family: Theme.mono
                    font.pixelSize: 11
                    elide: Text.ElideMiddle
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: 14
                    text: root.timesUsed(row.modelData.n)
                    color: root.timesUsed(row.modelData.n) > 0 ? Theme.inkDim : Theme.inkFaint
                    font.family: Theme.mono
                    font.pixelSize: 10
                }

                HoverHandler { id: rowHover }
                Carry { asset: row.modelData }
                }
            }
        }

    }
}
