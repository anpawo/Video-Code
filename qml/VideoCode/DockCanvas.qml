// The dock, drawn from a plan rather than from a tree of nested views.
//
// It used to be a SplitView holding DockNodes holding SplitViews. That reads
// well and it costs everything else: a QML Repeater over a JS array rebuilds
// its delegates whenever the array is replaced, so every structural change —
// a tab moved, a pane split, a handle released — destroyed every pane in the
// dock and built them again. Three consequences, all of them things you could
// feel:
//
//   · nothing could animate, because the items that would have animated did
//     not exist a moment ago;
//   · a resize could not be applied while the mouse was down, since rebuilding
//     the dock destroyed the grip under the pointer;
//   · the model and the items disagreed about sizes, so the dock read the
//     panes back to find out how big they were — and that reading was short by
//     the width of a splitter handle, which is how a 50/50 split became
//     51.1/48.9 after four tab clicks.
//
// So the tree is measured, once, into a flat plan: a rectangle per pane, a
// rectangle per handle. The plan feeds ListModels whose rows are keyed by node
// id, which means a pane KEEPS ITS ITEM across a change and only its geometry
// moves — and geometry that moves is geometry that can be animated. The model
// is the only truth about sizes; nothing is ever measured off the screen.
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls

Item {
    id: root

    // The dock's brain (Main.qml) and the tree to draw.
    property var dock: null
    property var node: null

    // The tree the POINTER is answered against — the committed one, never the
    // preview. They are the same object except while a tab is in the air, and
    // that exception is the whole point of the property.
    property var hitNode: null

    // Panes slide only while a tab is in the air. A handle being dragged must
    // answer the pointer on the same frame, and a window being resized has no
    // business sliding at all.
    // `!!dock`, not `dock !== null`: an unset property is `undefined`, which is
    // not null, and reading through it hands the binding an undefined bool.
    readonly property bool animating: !!dock && dock.tabInFlight === true

    readonly property real gap: Theme.gap

    // ── The plan ──────────────────────────────────────────────────────────
    // A pure function of the tree and this item's size. Recomputed by the
    // binding whenever either changes; nothing else in the dock needs to know
    // when that happens.
    // The size is read FIRST, on purpose. A binding only depends on what it
    // actually read, and a guard that short-circuits on the node never reads the
    // width — so the plan stopped following the window the moment it was
    // evaluated once with nothing to draw.
    readonly property var plan: {
        const w = root.width;
        const h = root.height;
        if (!root.node || w <= 4 || h <= 4)
            return { panes: [], handles: [], splits: [] };
        return root.measure(root.node, 0, 0, w, h);
    }

    // The same measurement, of the arrangement as it stands rather than as it
    // is about to be.
    //
    // Hit-testing against `plan` was a loop: the pointer picked a drop zone, the
    // preview opened a hole for it, every pane slid — and the pointer was then
    // over something else, which picked a different zone, which slid them back.
    // The layout oscillated at the animation's own frame rate for as long as the
    // tab was held. A drop target has to be a question about where the panes
    // ARE; asking it of where they are GOING makes the answer change the
    // question.
    readonly property var hitPlan: {
        const w = root.width;
        const h = root.height;
        const tree = root.hitNode ? root.hitNode : root.node;
        if (!tree || w <= 4 || h <= 4)
            return { panes: [], handles: [], splits: [] };
        return root.measure(tree, 0, 0, w, h);
    }

    function measure(node, x, y, w, h) {
        const out = { panes: [], handles: [], splits: [] };
        root.walk(node, x, y, w, h, out);
        return out;
    }

    function walk(node, x, y, w, h, out) {
        if (node.t !== "x") {
            out.panes.push({
                id: node.id, kind: node.t,
                keys: node.t === "s" ? node.keys : [],
                current: node.t === "s" ? node.current : 0,
                x: x, y: y, w: w, h: h
            });
            return;
        }

        out.splits.push({ id: node.id, dir: node.dir, x: x, y: y, w: w, h: h });

        const across = node.dir === "h";
        const total = across ? w : h;
        let pos = across ? x : y;

        for (let i = 0; i < node.nodes.length; i++) {
            const child = node.nodes[i];
            const last = i === node.nodes.length - 1;
            // The last child takes whatever is left, to the pixel. A size is a
            // fraction, fractions do not add up to a window, and a dock that is
            // three pixels short of its own edge is a dock with a seam in it.
            const extent = last
                         ? (across ? x + w : y + h) - pos
                         : Math.max(24, Math.round(child.size * total));

            if (across)
                root.walk(child, pos, y, extent, h, out);
            else
                root.walk(child, x, pos, w, extent, out);

            pos += extent;
            if (!last) {
                out.handles.push({
                    id: node.id + "|" + i, split: node.id, index: i, across: across,
                    x: across ? pos : x, y: across ? y : pos,
                    w: across ? root.gap : w, h: across ? h : root.gap
                });
                pos += root.gap;
            }
        }
    }

    // Where a pane is, by id — what the drop logic asks instead of hunting for
    // an item and asking IT.
    function rectOf(id) {
        for (const one of root.plan.panes)
            if (one.id === id)
                return one;
        return null;
    }

    function splitRect(id) {
        for (const one of root.plan.splits)
            if (one.id === id)
                return one;
        return null;
    }

    // ── Keeping the rows in step with the plan ────────────────────────────
    // A row is found by id and UPDATED; only what has appeared is inserted and
    // only what has gone is removed. That is the whole trick: the delegate for
    // a pane outlives every change that does not delete the pane.
    ListModel { id: paneRows }
    ListModel { id: handleRows }

    function sync() {
        root.reconcile(paneRows, root.plan.panes, (one) => ({
            nodeId: one.id, kind: one.kind, keysJson: JSON.stringify(one.keys),
            current: one.current, px: one.x, py: one.y, pw: one.w, ph: one.h
        }));
        root.reconcile(handleRows, root.plan.handles, (one) => ({
            nodeId: one.id, split: one.split, index: one.index, across: one.across,
            px: one.x, py: one.y, pw: one.w, ph: one.h
        }));
    }

    function reconcile(model, wanted, rowOf) {
        for (let i = model.count - 1; i >= 0; i--) {
            const id = model.get(i).nodeId;
            let alive = false;
            for (const one of wanted)
                if (one.id === id) {
                    alive = true;
                    break;
                }
            if (!alive)
                model.remove(i);
        }

        for (const one of wanted) {
            let at = -1;
            for (let i = 0; i < model.count; i++)
                if (model.get(i).nodeId === one.id) {
                    at = i;
                    break;
                }
            if (at < 0)
                model.append(rowOf(one));
            else
                model.set(at, rowOf(one));
        }
    }

    onPlanChanged: root.sync()
    Component.onCompleted: root.sync()

    // ── The panes ─────────────────────────────────────────────────────────
    // The delegate carries its own components. A `Component` declared at the
    // file's top level cannot see a delegate's scope — `pragma
    // ComponentBehavior: Bound` says so out loud — so a Panel built from one up
    // there is a Panel whose `keys` are nobody's keys.
    Repeater {
        model: paneRows

        Item {
            id: pane
            required property string nodeId
            required property string kind
            required property string keysJson
            required property int current
            required property real px
            required property real py
            required property real pw
            required property real ph

            x: pane.px
            y: pane.py
            width: pane.pw
            height: pane.ph

            Behavior on x { enabled: root.animating; NumberAnimation { duration: Theme.motion(150); easing.type: Easing.OutCubic } }
            Behavior on y { enabled: root.animating; NumberAnimation { duration: Theme.motion(150); easing.type: Easing.OutCubic } }
            Behavior on width { enabled: root.animating; NumberAnimation { duration: Theme.motion(150); easing.type: Easing.OutCubic } }
            Behavior on height { enabled: root.animating; NumberAnimation { duration: Theme.motion(150); easing.type: Easing.OutCubic } }

            Loader {
                anchors.fill: parent
                sourceComponent: pane.kind === "s" ? slotOf : (pane.kind === "p" ? holeOf : null)
            }

            // The room a tab in the air is about to take. Empty on purpose —
            // what goes in it is the pane under your hand, and drawing a copy of
            // it here would be two of the same thing on screen.
            Component {
                id: holeOf

                Rectangle {
                    color: Qt.alpha(Theme.live, 0.10)
                    border.width: 1
                    border.color: Qt.alpha(Theme.live, 0.75)
                    radius: Theme.radius
                    opacity: 0

                    Component.onCompleted: opacity = 1
                    Behavior on opacity { NumberAnimation { duration: Theme.motion(120) } }

                    Rectangle {
                        anchors.centerIn: parent
                        visible: parent.width > 80 && parent.height > 50
                        width: Math.min(parent.width - 28, 160)
                        height: 2
                        radius: 1
                        color: Qt.alpha(Theme.live, 0.7)
                    }
                }
            }

            Component {
                id: slotOf

                Panel {
                    slotId: pane.nodeId
                    keys: JSON.parse(pane.keysJson)
                    current: pane.current
                    measuring: root.dock.measuring
                    measureIn: root
                    titles: root.dock.panelTitles
                    items: root.dock.panelItems
                    dropZone: root.dock.hoverSlot === pane.nodeId ? root.dock.hoverZone : ""
                    gripRight: !root.dock.hasNeighbour(pane.nodeId, "right")
                    gripBottom: !root.dock.hasNeighbour(pane.nodeId, "bottom")

                    onEdgeResized: (side, delta) => root.dock.commitResize(pane.nodeId, side, delta)
                    // Screen coordinates on the way out, window coordinates on
                    // the way in: a pane pulled by its edge knows where the
                    // pointer is on the desktop, and the label is drawn in the
                    // window.
                    onSizeShown: (globalX, globalY, text) => {
                        const at = root.dock.contentItem.mapFromGlobal(globalX, globalY);
                        root.dock.showTip(at.x, at.y, text);
                    }
                    onSizeHidden: root.dock.hideTip()
                    onFloatRequested: root.dock.floatCurrent(pane.nodeId)
                    onTabPicked: (index) => root.dock.pickTab(pane.nodeId, index)
                    onTabClosed: (key) => root.dock.closeTab(pane.nodeId, key)
                    onMenuRequested: (x, y) => root.dock.openMenu(pane.nodeId, x, y)
                    onTabDragMoved: (x, y) => root.dock.dragOver(pane.nodeId, x, y)
                    onTabDropped: (key, x, y) => root.dock.drop(pane.nodeId, key, x, y)
                }
            }
        }
    }

    // ── The handles ───────────────────────────────────────────────────────
    // Empty until you point at one — a splitter is a thing you use, not a thing
    // you look at — and warm while it is held.
    //
    // The drag writes the MODEL on every move, which is new: it used to be
    // committed on release only, because moving a boundary rebuilt the dock and
    // took the grip out from under the pointer. Nothing is rebuilt now.
    Repeater {
        model: handleRows

        Rectangle {
            id: bar
            required property string nodeId
            required property string split
            required property int index
            required property bool across
            required property real px
            required property real py
            required property real pw
            required property real ph

            x: bar.px
            y: bar.py
            width: bar.pw
            height: bar.ph
            z: 5

            color: grab.pressed ? Theme.live : (grab.containsMouse ? Theme.edge : "transparent")
            Behavior on color { ColorAnimation { duration: Theme.motion(90) } }

            Behavior on x { enabled: root.animating; NumberAnimation { duration: Theme.motion(140); easing.type: Easing.OutCubic } }
            Behavior on y { enabled: root.animating; NumberAnimation { duration: Theme.motion(140); easing.type: Easing.OutCubic } }
            Behavior on width { enabled: root.animating; NumberAnimation { duration: Theme.motion(140); easing.type: Easing.OutCubic } }
            Behavior on height { enabled: root.animating; NumberAnimation { duration: Theme.motion(140); easing.type: Easing.OutCubic } }

            MouseArea {
                id: grab
                anchors.fill: parent
                anchors.margins: -2
                hoverEnabled: true
                cursorShape: bar.across ? Qt.SplitHCursor : Qt.SplitVCursor
                preventStealing: true

                property real anchorAt: 0

                onPressed: (mouse) => {
                    const at = mapToItem(root, mouse.x, mouse.y);
                    anchorAt = bar.across ? at.x : at.y;
                }

                onPositionChanged: (mouse) => {
                    if (!pressed)
                        return;
                    const at = mapToItem(root, mouse.x, mouse.y);
                    const now = bar.across ? at.x : at.y;
                    root.dock.dragHandle(bar.split, bar.index, now - anchorAt);
                    anchorAt = now;

                    // What each side holds, while you are deciding. Aiming for
                    // "a third of the window" is otherwise a matter of dragging,
                    // letting go, looking, and dragging again.
                    const where = mapToItem(root.dock.contentItem, mouse.x, mouse.y);
                    root.dock.showTip(where.x, where.y,
                                      root.dock.shareAt(bar.split, bar.index));
                }

                onReleased: root.dock.hideTip()
                onCanceled: root.dock.hideTip()
            }
        }
    }
}
