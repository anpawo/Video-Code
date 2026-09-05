// A dock slot: a tab strip over a body.
//
// A slot does NOT own the panels it shows. It is handed the keys it currently
// holds and the shared table of panel items, and the dock model in Main.qml is
// the only truth about where each panel lives. That is what makes a tab dragged
// from one slot to another a single change to one tree: both slots re-read the
// model and reparent whatever is theirs now.
//
// The active tab is marked on TOP, where the eye already is, rather than
// underlined like a web tab.
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Window

Rectangle {
    id: root

    // Which slot of the dock tree this is, and what the model says it holds.
    property string slotId: ""
    property var keys: []
    property int current: 0

    // key → label and key → Item, shared by every slot.
    property var titles: ({})
    property var items: ({})

    // Blank the pane and write what share of the window it takes. Set by the
    // dock, for every slot at once — one pane's percentage means nothing next to
    // panes still showing their contents.
    property bool measuring: false

    // The dock's own area — everything the panes divide between them, and the
    // only honest denominator for a share.
    property Item measureIn: null

    // The two figures, taken rather than bound.
    //
    // A share needs the pane's position inside the dock, and `mapToItem` is a
    // CALL, not an expression QML can track: a binding that uses it never hears
    // that the item moved. The belt's timeline was still reporting the x it had
    // during an intermediate layout pass — 128 instead of 342 — which is how a
    // row came back as 99,9 with no rounding error in sight. Taken when the
    // reading is asked for, and again if a pane changes size while it is up.
    property string shareWidth: ""
    property string shareHeight: ""

    function readShares() {
        if (!measuring)
            return;
        shareWidth = share("width");
        shareHeight = share("height");
    }

    onMeasuringChanged: readShares()
    onWidthChanged: readShares()
    onHeightChanged: readShares()

    // Where a tab would land if it were dropped now: "", "center", "left",
    // "right", "top" or "bottom". Set by the dock while a drag is overhead.
    property string dropZone: ""

    readonly property bool empty: keys.length === 0

    // The strip's parking space for a control lent by the panel on show.
    readonly property Item extraSlot: extras
    // How far the pointer travels before pressing a tab becomes moving it.
    // Written here rather than read from Qt.styleHints, which qmllint cannot
    // type-check, and a tab strip wants a shorter fuse than a file manager.
    readonly property int dragThreshold: 6
    readonly property string currentKey: current >= 0 && current < keys.length ? keys[current] : ""

    // Whether this pane has room to give on that side. Where it has not, the
    // dock puts a grip: an edge you can still pull in, because a pane must be
    // shrinkable even when nothing is waiting to take the space.
    property bool gripRight: false
    property bool gripBottom: false

    signal edgeResized(string side, real delta)

    // Where the pointer is while an edge is being pulled, and what the pane would
    // measure if it were let go there. The dock draws it: the label belongs to
    // the gesture, not to the pane, and the pane is the one thing on screen that
    // cannot draw outside its own edges.
    signal sizeShown(real globalX, real globalY, string text)
    signal sizeHidden()
    signal floatRequested()

    signal tabPicked(int index)
    signal tabClosed(string key)
    signal menuRequested(real globalX, real globalY)
    signal tabDragMoved(real globalX, real globalY)
    signal tabDropped(string key, real globalX, real globalY)

    color: Theme.panel
    // Three states on one pixel, in order of urgency: a tab about to land here,
    // the keyboard being here, and neither.
    border.color: dropZone !== "" ? Theme.live : (holdsFocus ? Theme.focusEdge : Theme.edge)
    border.width: 1
    radius: Theme.radius

    // ── Which pane the keys are going to ──────────────────────────────────
    // Five panes and one keyboard: Space plays or writes a space depending on
    // where the caret is, ⌘← goes back a file or nothing at all. That is only
    // fair if the window says where it is, and one gold edge says it without
    // moving anything or adding a widget.
    //
    // Asked of the window rather than kept as state: focus moves for reasons no
    // slot can see — a panel reparented into another slot, a dialog closing,
    // an item hidden behind a tab losing it silently — and a flag would go
    // stale on every one of them.
    readonly property Item focusedItem: Window.window !== null ? Window.window.activeFocusItem : null
    readonly property bool holdsFocus: {
        let item = focusedItem;
        while (item !== null) {
            if (item === body)
                return true;
            item = item.parent;
        }
        return false;
    }

    onKeysChanged: syncBody()
    onCurrentChanged: syncBody()
    Component.onCompleted: syncBody()

    // What this pane takes of the dock, along one axis.
    //
    // Measured against the DOCK, not the window: the window also holds the
    // status strip and the dock's own outer margin, and a pane charged for
    // pixels no pane can ever occupy gives a row that adds up to 98 — a number
    // you cannot reason with, which is the whole point of showing it.
    //
    // Each pane is measured WITH the splitter that follows it, against a dock
    // one splitter wider than it really is. That tiles exactly, whatever the
    // number of panes in the row: pane i ends where pane i+1 begins, the first
    // starts at zero and the last ends at the far edge — so a row adds up to 100
    // by construction rather than by luck. (Half a gap to each side, which is
    // the obvious rule, does NOT tile: the two halves at the outer edges have no
    // pane to belong to, and the row came back as 100,3.)
    //
    // And the rounding is done on the BOUNDARIES rather than on each share, so
    // two panes at 48,5% do not come back as 49 + 49 = 98. Each share is the
    // difference between two rounded edges, which sums exactly — tenths
    // included.
    //
    // A tenth rather than a whole percent because this number is read WHILE a
    // splitter moves: at whole percents it sits still for fifteen pixels and
    // then jumps, which reads as a control that is not following your hand. A
    // tenth changes every pixel and a half. A hundredth would change on every
    // pixel and the last digit would be noise.
    function share(axis) {
        if (measureIn === null || measureIn.width <= 0 || measureIn.height <= 0)
            return "—";

        const across = axis === "width";
        const whole = (across ? measureIn.width : measureIn.height) + Theme.gap;
        const at = root.mapToItem(measureIn, 0, 0);

        let near = across ? at.x : at.y;
        let far = near + (across ? root.width : root.height) + Theme.gap;

        // A pane against the dock's edge IS against it. Fractional pane sizes
        // leave the last one ending a pixel and a half short of the far side,
        // which is nothing to look at and a tenth of a percent to read — the row
        // came back as 99,9. Anything within a gap of an edge is snapped to it,
        // and a split layout never puts a pane that close to the edge without
        // touching it.
        if (near < Theme.gap)
            near = 0;
        if (far > whole - Theme.gap)
            far = whole;

        const percent = Math.round(far / whole * 1000) / 10 - Math.round(near / whole * 1000) / 10;
        return root.percent(percent);
    }

    // One tenth, with a comma. The separator is a choice about how the number
    // READS, and it is written in one place so the pane, the splitter and the
    // edge grip cannot drift into three conventions.
    function percent(value) {
        return value.toFixed(1).replace(".", ",") + "%";
    }

    // Everything this slot holds is parented into its body; only the current tab
    // is shown. A panel that has left for another slot is not touched here — the
    // slot that took it reparents it, so the two never fight over one item.
    function syncBody() {
        for (let i = 0; i < keys.length; i++) {
            const item = items[keys[i]];
            if (!item)
                continue;
            item.parent = body;
            item.anchors.fill = body;
            item.visible = i === current;

            // A panel may hand ONE control up into the tab strip — the timeline's
            // zoom is the case that asked for it. It goes to the slot showing the
            // panel, and only while it is the tab on top, so a control never
            // outlives the thing it controls or floats over a stranger's tabs.
            const lent = item.stripControl;
            if (!lent || !root.extraSlot)
                continue;
            if (i === current) {
                lent.parent = root.extraSlot;
                lent.anchors.verticalCenter = root.extraSlot.verticalCenter;
                lent.anchors.left = root.extraSlot.left;
                lent.visible = true;
            } else {
                lent.visible = false;
            }
        }
    }

    Rectangle {
        id: strip
        anchors { left: parent.left; right: parent.right; top: parent.top }
        anchors.margins: 1
        height: 27
        color: Theme.rail
        topLeftRadius: Theme.radiusInner
        topRightRadius: Theme.radiusInner

        TapHandler {
            acceptedButtons: Qt.RightButton
            onTapped: (point) => {
                const at = strip.mapToGlobal(point.position.x, point.position.y);
                root.menuRequested(at.x, at.y);
            }
        }

        Row {
            anchors.fill: parent
            spacing: 0

            Repeater {
                model: root.keys

                Rectangle {
                    id: tab
                    required property int index
                    required property string modelData
                    readonly property bool active: root.current === tab.index

                    width: label.implicitWidth + (tab.active ? 44 : 22)
                    height: strip.height
                    color: "transparent"
                    // A tab being carried elsewhere fades where it came from, so
                    // it is obvious which one is in flight.
                    opacity: tabMouse.dragging ? 0.4 : 1

                    // The tab you are on, as a capsule inside the strip rather
                    // than a slab flush with it. That is what the system's own
                    // segmented controls do, and it is what lets the strip read
                    // as one control with a selection instead of as a row of
                    // boxes with one of them lit.
                    Rectangle {
                        id: seat
                        visible: tab.active
                        anchors.fill: parent
                        anchors.topMargin: 3
                        anchors.bottomMargin: 3
                        anchors.leftMargin: 2
                        anchors.rightMargin: 2
                        radius: Theme.pill(height)
                        color: Theme.panel
                        border.width: 1
                        border.color: Theme.edgeSoft
                    }

                    // The accent stays, and stays meaning the same thing — this
                    // is the pane the keys are talking to. A dot inside the
                    // capsule rather than a bar across the top of it: a rule
                    // over a rounded seat cuts its corner off.
                    Rectangle {
                        visible: tab.active
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 11
                        width: 5
                        height: 5
                        radius: 2.5
                        color: Theme.live
                    }

                    Text {
                        id: label
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: tab.active ? 22 : 11
                        text: root.titles[tab.modelData] !== undefined
                              ? root.titles[tab.modelData]
                              : tab.modelData
                        color: tab.active
                               ? Theme.ink
                               : (tabMouse.containsMouse ? Theme.inkDim : Theme.inkFaint)
                        font.family: Theme.ui
                        font.pixelSize: 12
                    }

                    // Only the tab you are looking at can be closed, so a stack of
                    // tabs is not a row of little targets to misfire on.
                    Text {
                        id: closer
                        visible: tab.active
                        // Above the tab's own MouseArea, which is declared after
                        // it and would otherwise swallow every click meant for
                        // the ×: the topmost item wins, not the smallest.
                        z: 1
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: parent.right
                        anchors.rightMargin: 8
                        text: "×"
                        color: closeMouse.containsMouse ? Theme.ink : Theme.inkFaint
                        font.family: Theme.ui
                        font.pixelSize: 14

                        MouseArea {
                            id: closeMouse
                            anchors.centerIn: parent
                            // The × is drawn at 14 px because a big one would
                            // shout; what you AIM at is the full height of the
                            // strip, which is the smallest target this chrome is
                            // allowed to ask a pointer to hit.
                            width: 24; height: strip.height
                            hoverEnabled: true
                            onClicked: root.tabClosed(tab.modelData)
                        }
                    }

                    // Separator between tabs — and never beside the selected
                    // one, whose capsule already separates it. A hairline
                    // touching a rounded seat reads as a crack in it.
                    Rectangle {
                        visible: tab.index < root.keys.length - 1 && !tab.active
                                 && root.current !== tab.index + 1
                        anchors { right: parent.right; top: parent.top; bottom: parent.bottom }
                        width: 1
                        color: Theme.edgeSoft
                    }

                    // Selecting and moving a tab are the same gesture until the
                    // pointer travels far enough to be a drag, so ONE MouseArea
                    // decides which it was — not a TapHandler beside a
                    // DragHandler.
                    //
                    // That pairing looks right and is what the handler docs
                    // suggest, but here the DragHandler took the exclusive grab
                    // on press and the tap never fired: the tabs quietly stopped
                    // being clickable while dragging still worked. A MouseArea
                    // has no arbitration to lose.
                    //
                    // Positions leave in GLOBAL coordinates because the drop may
                    // land in another window: a scene position means nothing to a
                    // floating panel three hundred pixels off the main one.
                    MouseArea {
                        id: tabMouse
                        anchors.fill: parent
                        hoverEnabled: true

                        property point origin
                        property bool dragging: false

                        onPressed: (mouse) => {
                            tabMouse.origin = Qt.point(mouse.x, mouse.y);
                            tabMouse.dragging = false;
                        }

                        onPositionChanged: (mouse) => {
                            if (!tabMouse.pressed)
                                return;
                            const travelled = Math.hypot(mouse.x - tabMouse.origin.x,
                                                         mouse.y - tabMouse.origin.y);
                            if (!tabMouse.dragging && travelled < root.dragThreshold)
                                return;
                            tabMouse.dragging = true;
                            const at = tab.mapToGlobal(mouse.x, mouse.y);
                            root.tabDragMoved(at.x, at.y);
                        }

                        onReleased: (mouse) => {
                            const at = tab.mapToGlobal(mouse.x, mouse.y);
                            if (tabMouse.dragging)
                                root.tabDropped(tab.modelData, at.x, at.y);
                            else
                                root.tabPicked(tab.index);
                            tabMouse.dragging = false;
                        }

                        // A grab lost to something else (a window moving under the
                        // pointer, a modal opening) abandons the move rather than
                        // dropping the panel somewhere nobody aimed at. The
                        // impossible position clears the dock's highlight.
                        onCanceled: {
                            tabMouse.dragging = false;
                            root.tabDragMoved(-1, -1);
                        }
                    }
                }
            }
        }

        // An emptied slot only exists while something is being dragged over it;
        // the dock prunes it otherwise. It still says what it is, rather than
        // looking like a panel that failed to draw.
        Text {
            visible: root.empty
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 11
            text: "Drop a tab here"
            color: Theme.inkFaint
            font.family: Theme.ui
            font.pixelSize: 11
            font.italic: true
        }

        // Where a panel's own control lands, between the tabs and the ⋯ menu.
        Item {
            id: extras
            anchors {
                right: tool.left; rightMargin: 6
                verticalCenter: parent.verticalCenter
            }
            // Sized by the control it holds, read straight off it: binding to
            // childrenRect while the child anchors to this item's own right edge
            // is a loop, and Qt breaks it by leaving the width at zero.
            width: children.length > 0 ? children[0].width : 0
            height: parent.height
        }

        // Out of the window, into one of its own — the two overlapping frames
        // every application uses for this. It replaced the ⋯ because floating a
        // panel is the thing you reach for here, and a menu that has to be opened
        // to find it is one click too many; the menu itself is now the right
        // button, on the strip, where a context menu belongs.
        Rectangle {
            id: tool
            anchors { right: parent.right; top: parent.top; bottom: parent.bottom }
            width: 26
            color: toolHover.hovered ? Theme.panel : "transparent"
            topRightRadius: Theme.radiusInner

            Item {
                anchors.centerIn: parent
                width: 13
                height: 13

                Rectangle {
                    x: 4; y: 0
                    width: 9; height: 7
                    color: "transparent"
                    border.width: 1
                    border.color: toolHover.hovered ? Theme.ink : Theme.inkFaint
                    radius: 1
                }

                Rectangle {
                    x: 0; y: 5
                    width: 9; height: 8
                    color: toolHover.hovered ? Theme.panel : Theme.rail
                    border.width: 1
                    border.color: toolHover.hovered ? Theme.ink : Theme.inkFaint
                    radius: 1
                }
            }

            HoverHandler { id: toolHover }
            TapHandler { onTapped: root.floatRequested() }
        }

        Rectangle {
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            height: 1
            color: Theme.edge
        }
    }

    Item {
        id: body
        anchors {
            left: parent.left; right: parent.right
            top: strip.bottom; bottom: parent.bottom
            margins: 1
        }
        clip: true

        // What this pane is, as a number.
        //
        // Over the contents rather than instead of them: the panel keeps its
        // children alive and its scroll positions intact, so the reading costs
        // nothing to take and nothing to put away.
        Rectangle {
            anchors.fill: parent
            z: 200
            visible: root.measuring
            color: Theme.panel

            Column {
                anchors.centerIn: parent
                spacing: 4

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    // Named, because two bare percentages side by side leave you
                    // to work out which axis is which — and the ancestors of the
                    // two numbers are not the same thing at all.
                    textFormat: Text.StyledText
                    text: "<font color=\"" + Theme.inkFaint + "\">w</font> " + root.shareWidth
                          + "  ×  <font color=\"" + Theme.inkFaint + "\">h</font> " + root.shareHeight
                    color: Theme.ink
                    font.family: Theme.mono
                    font.pixelSize: 15
                }

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: Math.round(root.width) + " × " + Math.round(root.height) + " px"
                    color: Theme.inkFaint
                    font.family: Theme.mono
                    font.pixelSize: 11
                }
            }
        }

        // A press anywhere in the pane means you are working in THIS pane.
        //
        // The picture, the timeline and the code pane already claim the keyboard
        // when clicked; the media browser and the agent's transcript have no
        // reason of their own to, and without this a click on either would leave
        // the keys — and the gold edge — with whatever pane you were in before.
        //
        // Over the content rather than under it, and refusing the press it just
        // saw: under it, a panel with a MouseArea of its own would swallow the
        // press first and this would never run. Declining the event lets it fall
        // through unchanged, so a panel that DOES want the keyboard still takes
        // it a moment later, and one that does not leaves it here.
        MouseArea {
            id: floor
            anchors.fill: parent
            z: 100
            acceptedButtons: Qt.AllButtons
            onPressed: (mouse) => {
                floor.forceActiveFocus();
                mouse.accepted = false;
            }
        }
    }

    // ── Edges you can pull ────────────────────────────────────────────────
    // Only on the sides with no neighbour: everywhere else the dock's own
    // splitter already sits in the gap between two panes, and two things to grab
    // in the same place is one too many.
    // How far the edge has been pulled, while it is being pulled. The pane is not
    // resized yet — this is what the preview below draws.
    property real dragOffset: 0
    property string dragSide: ""

    component Grip: MouseArea {
        property string side: ""
        property real lastX: 0
        property real lastY: 0

        hoverEnabled: true

        onPressed: (mouse) => {
            const at = mapToGlobal(mouse.x, mouse.y);
            lastX = at.x;
            lastY = at.y;
            root.dragSide = side;
            root.dragOffset = 0;
        }

        onPositionChanged: (mouse) => {
            if (!pressed)
                return;
            const at = mapToGlobal(mouse.x, mouse.y);
            const step = side === "right" ? at.x - lastX : at.y - lastY;
            lastX = at.x;
            lastY = at.y;
            // Only inwards, and never past the point where the pane would have
            // nothing left to show.
            const room = (side === "right" ? root.width : root.height) - 80;
            root.dragOffset = Math.max(-room, Math.min(0, root.dragOffset + step));

            // The size it would BE, not the size it is: the pane does not move
            // until you let go, and a number that lags the pointer by a whole
            // gesture is a number you cannot aim with.
            const wide = side === "right";
            const next = (wide ? root.width : root.height) + root.dragOffset;
            const whole = root.measureIn === null
                          ? 0
                          : (wide ? root.measureIn.width : root.measureIn.height) + Theme.gap;
            root.sizeShown(at.x, at.y,
                           (wide ? "w " : "h ")
                           + (whole > 0 ? root.percent((next + Theme.gap) / whole * 100) : "—")
                           + "   " + Math.round(next) + " px");
        }

        onReleased: {
            root.edgeResized(side, root.dragOffset);
            root.dragOffset = 0;
            root.dragSide = "";
            root.sizeHidden();
        }
    }

    Grip {
        side: "right"
        visible: root.gripRight
        anchors { right: parent.right; top: parent.top; bottom: parent.bottom }
        width: 6
        cursorShape: Qt.SizeHorCursor
    }

    Grip {
        side: "bottom"
        visible: root.gripBottom
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 6
        cursorShape: Qt.SizeVerCursor
    }

    // The room about to be given up, shown as it is being given up.
    Rectangle {
        visible: root.dragOffset < 0
        z: 12
        color: Qt.alpha(Theme.ground, 0.72)
        border.width: 1
        border.color: Theme.live
        radius: Theme.radiusInner

        x: root.dragSide === "right" ? root.width + root.dragOffset : 0
        y: root.dragSide === "bottom" ? root.height + root.dragOffset : 0
        width: root.dragSide === "right" ? -root.dragOffset : root.width
        height: root.dragSide === "bottom" ? -root.dragOffset : root.height
    }

    // ── Where the drop would land ─────────────────────────────────────────
    // Shown as the shape the panel would take, not as an arrow or a hint: the
    // half of the slot that is about to become the new pane lights up, so what
    // you see under the cursor is what you get when you let go.
    // Where a dropped tab would land — the TAB case only.
    //
    // A drop that splits this pane is not drawn here any more: the dock opens a
    // real hole in the layout for it, and a rectangle over the pane saying the
    // same thing in worse terms would be the second answer to one question.
    // Landing in the strip moves nothing, so it has nothing to show but itself.
    Rectangle {
        visible: root.dropZone === "center"
        anchors.fill: parent
        anchors.margins: 2
        z: 10
        color: Qt.alpha(Theme.live, 0.14)
        border.color: Theme.live
        border.width: 1
        radius: Theme.radiusInner
    }
}
