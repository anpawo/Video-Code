// The shape of a change, as four numbers you can pull.
//
// `easing=CubicBezier(0.42, 0, 0.58, 1)` is a line of Python nobody can
// picture. Here it is the picture: time across, how far along up, and the two
// control points exactly where the call puts them. A preset is the same four
// numbers — `Easing.Out` IS a `CubicBezier` — so choosing one moves these
// handles rather than swapping the drawing for a word.
//
// Drawn as a run of short bars, not on a `Canvas`. A Canvas paints on a polish
// and shows on the frame after it, and an effect row's chip is built when the
// card opens — after the frame that would have painted it. Measured: the chips
// that existed before the card opened were drawn, the ones the opening made
// stayed blank, and no amount of asking for a repaint reached them. Rectangles
// are in the scene graph the moment they are bound, and a binding is also what
// makes the shape follow the pointer for free while a handle is dragged.
//
// Both control points stay inside the square. That rules out the overshoot
// curves an editor would otherwise draw, and it is on purpose: the easings that
// go past 1 in this library (`Back`, `Elastic`, `Bounce`) are `Func`s, not
// beziers, so no curve here could have been dragged into one anyway.
pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: root

    // x1, y1, x2, y2 — the two control points, in the unit square.
    property var handles: [0.42, 0.0, 0.58, 1.0]
    property color tint: Theme.live
    property bool interactive: false

    // Let go, not moved: the source is written on release. A scene that re-runs
    // on every mouse move is a scene that never finishes running, and the shape
    // under the pointer already says what the release will write.
    signal letGo()

    readonly property real inset: interactive ? 10 : 3
    readonly property int steps: interactive ? 24 : 12

    // Unit square → pixels, with the origin where a graph puts it: bottom left.
    function at(px, py) {
        return [inset + px * (width - inset * 2), height - inset - py * (height - inset * 2)];
    }

    function pointAt(t) {
        const p = handles;
        const u = 1 - t;
        return at(
            3 * u * u * t * p[0] + 3 * u * t * t * p[2] + t * t * t,
            3 * u * u * t * p[1] + 3 * u * t * t * p[3] + t * t * t
        );
    }

    function moveHandle(which, px, py) {
        const x = Math.round(Math.max(0, Math.min(1, px)) * 100) / 100;
        const y = Math.round(Math.max(0, Math.min(1, py)) * 100) / 100;
        const next = root.handles.slice();
        next[which * 2] = x;
        next[which * 2 + 1] = y;
        root.handles = next;
    }

    // A straight bar between two points. Anchored at its left edge and turned
    // about it, so `a` is where it starts however the two points lie, and run a
    // hair past `b` so the joint with the next one does not show as a bead. The
    // last of a run says `extend: 0` — that overhang is what put the end of the
    // curve through the corner of the box.
    component Segment: Rectangle {
        required property var a
        required property var b
        property real weight: 1
        property real extend: weight

        x: a[0]
        y: a[1] - weight / 2
        width: Math.hypot(b[0] - a[0], b[1] - a[1]) + extend
        height: weight
        radius: weight / 2
        transformOrigin: Item.Left
        rotation: Math.atan2(b[1] - a[1], b[0] - a[0]) * 180 / Math.PI
        antialiasing: true
    }

    Rectangle {
        x: root.inset
        y: root.inset
        width: Math.max(root.width - root.inset * 2, 0)
        height: Math.max(root.height - root.inset * 2, 0)
        color: "transparent"
        border.width: 1
        border.color: Theme.edge
    }

    // The straight line the curve is read against: without it a gentle ease and
    // a linear one are the same picture.
    Segment {
        a: root.at(0, 0)
        b: root.at(1, 1)
        extend: 0
        color: Qt.alpha(Theme.inkFaint, 0.45)
    }

    Segment {
        visible: root.interactive
        a: root.at(0, 0)
        b: root.at(root.handles[0], root.handles[1])
        extend: 0
        color: Qt.alpha(root.tint, 0.5)
    }

    Segment {
        visible: root.interactive
        a: root.at(1, 1)
        b: root.at(root.handles[2], root.handles[3])
        extend: 0
        color: Qt.alpha(root.tint, 0.5)
    }

    Repeater {
        model: root.steps

        Segment {
            required property int index

            a: root.pointAt(index / root.steps)
            b: root.pointAt((index + 1) / root.steps)
            weight: root.interactive ? 2 : 1.5
            extend: index === root.steps - 1 ? 0 : weight
            color: root.tint
        }
    }

    Repeater {
        model: root.interactive ? 2 : 0

        Rectangle {
            required property int index

            readonly property var where: root.at(root.handles[index * 2],
                                                 root.handles[index * 2 + 1])
            x: where[0] - 5
            y: where[1] - 5
            width: 10
            height: 10
            radius: 5
            color: pull.holding === index ? Theme.ink : root.tint
            antialiasing: true
        }
    }

    // One area for both points rather than a hit box on each: a synthetic drag
    // presses where it starts and moves without ever hovering, so the point has
    // to be chosen from the press itself — the nearer of the two.
    MouseArea {
        id: pull
        anchors.fill: parent
        enabled: root.interactive
        cursorShape: Qt.PointingHandCursor

        property int holding: -1

        function unit(mouse) {
            const w = Math.max(width - root.inset * 2, 1);
            const h = Math.max(height - root.inset * 2, 1);
            return [(mouse.x - root.inset) / w, (height - root.inset - mouse.y) / h];
        }

        onPressed: (mouse) => {
            const here = unit(mouse);
            const p = root.handles;
            const first = Math.hypot(here[0] - p[0], here[1] - p[1]);
            const second = Math.hypot(here[0] - p[2], here[1] - p[3]);
            holding = first <= second ? 0 : 1;
            root.moveHandle(holding, here[0], here[1]);
        }

        onPositionChanged: (mouse) => {
            if (holding < 0)
                return;
            const here = unit(mouse);
            root.moveHandle(holding, here[0], here[1]);
        }

        onReleased: {
            holding = -1;
            root.letGo();
        }
    }
}
