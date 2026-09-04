// One lane per element, ordered by when it starts — so a longer edit reads as a
// staircase going down and no two things ever share a line.
//
// No left-hand name column: the bar already says what it is, and a second copy
// of the same name is the one thing a timeline never needs twice.
//
// A video is a SINGLE element carrying picture and sound together, drawn as one
// bar with its waveform inside. Splitting it across two lanes would be two rows
// for one object, which is exactly what this rule forbids.
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls

Item {
    id: root

    // The scene being shown, and what the user has picked out of it.
    required property var scene
    property int selectedIndex: -1
    property real playhead: 0

    // The range being worked on, in seconds, or -1 for "not set". Drawn rather
    // than obeyed: what it MEANS — play stops there — belongs to the transport.
    property real markIn: -1
    property real markOut: -1

    readonly property bool ranged: markIn >= 0 && markOut > markIn

    // The moments a trim prefers over the tenth it happens to land on: where
    // other clips begin and end, where the scene waits, where the playhead is.
    // Filled by the shell, which is the only thing that can see all of them.
    property var snapPoints: []

    // The moment nearest `seconds` worth snapping to, or the tenth it rounds to.
    // Eight pixels of forgiveness, so the magnet is the same size on screen at
    // every zoom — and none at all when ⌘ is held.
    function snapped(seconds, exact) {
        if (exact)
            return Math.round(seconds * 100) / 100;

        const reach = 8 / Math.max(root.pxPerSecond, 1);
        let best = -1;
        let near = reach;
        for (const one of root.snapPoints) {
            const d = Math.abs(one - seconds);
            if (d < near) {
                near = d;
                best = one;
            }
        }
        return best >= 0 ? Math.round(best * 100) / 100 : Math.round(seconds * 10) / 10;
    }

    signal elementPicked(int index)

    // A clip was opened, and this is where it sits on screen. The rect is the
    // whole point: whatever opens it can start there.
    signal elementOpened(var element, rect where)
    signal scrubbed(real seconds)

    // The element that is currently open in the middle of the window, by name.
    //
    // Its bar is not drawn here while it is out — it is somewhere else on screen,
    // and one element cannot be in two places. What stays is the outline of where
    // it was: the lane keeps its height and its grid, nothing reflows, and the
    // hollow says where it is going back to.
    property string openedName: ""

    // A moment under a pointer that is somewhere else in the window: what a
    // template being carried over the timeline is worth. Negative when the point
    // is not over the lanes at all, which is how a drop elsewhere does nothing.
    function timeAtWindow(x, y) {
        const at = flick.mapFromItem(null, x, y);
        if (at.x < 0 || at.y < 0 || at.x > flick.width || at.y > flick.height)
            return -1;
        return Math.max(0, (at.x + flick.contentX - root.pad) / root.pxPerSecond);
    }

    // Which element's lane is under a point, or null. An effect is always an
    // effect ON something, so a drop that is not over a clip means nothing —
    // and saying so beats applying it to whatever was last selected.
    function elementAtWindow(x, y) {
        const at = lanes.mapFromItem(null, x, y);
        if (at.x < 0 || at.y < 0 || at.x > lanes.width)
            return null;
        const row = Math.floor(at.y / root.laneHeight);
        if (row < 0 || row >= root.scene.elements.length)
            return null;
        return root.scene.elements[row];
    }

    // Which lane the pointer is over while something is carried, by index, so
    // it can be lit. -1 for none.
    property int hoverLane: -1

    // Where a carried thing would land, in seconds, or -1 for nothing carried.
    // Drawn, because a drop you cannot aim is a drop you undo.
    property real dropAt: -1

    // A clip's edge was dragged to a moment. What that MEANS is the shell's
    // business, not the timeline's: a video ends by loading fewer frames, a
    // square ends by being hidden, and both are one line of Python — see
    // Main.trimElement.
    signal trimmed(var element, string edge, real seconds)

    // A gap you can change. The band knows the line it was written on, so
    // clicking it is an edit to that line and nothing else — see Main.writeWait.
    signal waitChanged(int line, string seconds)

    // Which gap is being typed into, by line. Nothing else can be open at once:
    // two fields over a timeline is two answers to "what am I editing".
    property int editingWait: -1

    readonly property real pxPerSecond: zoom.value

    // A scene shorter than the pane draws a sliver — two seconds at 80 px/s is
    // 160 px of timeline in 1400 px of panel — and a sliver reads as a timeline
    // that has been cut off rather than as a video that is short. So the zoom has
    // a FLOOR: however long the scene lasts, it is drawn 95% of the panel wide.
    // The clips ARE the pane at that point, and the sliver of ground left at each
    // end is what says the scene stops there rather than running past the edge.
    //
    // That last part is why it is not the full width: the margin is never allowed
    // below `minPad`, whatever the pane is doing. On a narrow pane 5% would be a
    // couple of pixels, which reads as a clip touching the border — the same
    // "cut off" the floor exists to prevent, at the other end of the scale.
    //
    // It is the slider's `from`, not a clamp laid over the top of it. A clamp
    // would leave the handle sitting somewhere the picture does not agree with,
    // and half the slider's travel doing nothing; as the range's start, the
    // handle means what it shows — the range simply begins where the picture
    // stops being a sliver.
    readonly property int minPad: 10
    readonly property real fitWidth: Math.max(0, Math.min(width * 0.95, width - gutter - 2 * minPad))
    readonly property real fitZoom: span > 0 ? fitWidth / span : 0

    // And a CEILING, which the floor above yields to. Two numbers, because they
    // answer two questions:
    //
    //   `minSpan`      — what is on screen when nothing has been zoomed: ten
    //                    seconds, however short the scene.
    //   `tightestSpan` — as far in as the slider will ever go: five seconds,
    //                    which is exactly twice `minSpan` and is the whole of
    //                    the travel the handle has on a short scene.
    //
    // Ten at rest is what makes the ruler mean something. Blown up to fill the
    // pane, a four-second scene is drawn at five hundred pixels a second — every
    // clip is enormous, a tenth of a second is fifty pixels, and dragging an edge
    // moves it further than you meant. Five is as close as it is ever useful to
    // get: past that the numbers along the top stop reading as time.
    //
    // The trade, said plainly because it contradicts the paragraph above: a
    // scene shorter than ten seconds no longer fills the pane. It sits in a
    // ten-second ruler with the rest of it empty — which is what every editor
    // shows for a short clip, and it says "this is four seconds long" far better
    // than a bar touching both edges ever did.
    readonly property real minSpan: 10
    readonly property real tightestSpan: 5

    // What the timeline DRAWS: the scene, or ten seconds, whichever is longer.
    // One name for it, because the ruler's ticks, the lanes and the scroll
    // extent all have to agree — they used to be written separately against
    // `scene.duration`, which is why a ruler asked to run ten seconds still
    // stamped a number only as far as the scene went.
    readonly property real span: Math.max(scene.duration, minSpan)
    readonly property real maxZoom: fitWidth > 0 ? fitWidth / tightestSpan : 0


    readonly property real contentWidth: span * pxPerSecond
    readonly property int laneHeight: 48
    // Blank strip kept to the left of time zero. Wide enough for the playhead's
    // handle to sit at 0 without touching the panel's edge — and, since every
    // ruler stamp is centred on the line it names, wide enough for the FIRST one
    // to centre like the others instead of being nudged right by the clamp
    // below: half of "00:00" at 11px mono is about 17.
    readonly property int gutter: 22

    // A short scene at a low zoom does not fill the pane, and pinned to the left
    // it reads as a timeline that has been cut off — the empty half looks like
    // more time that is missing rather than time that does not exist. Centred,
    // the whole of it is the whole of it. Measured against the PANEL's width, not
    // the viewport's, or the margin below would feed back into the width it is
    // computed from.
    readonly property real centrePad: Math.max(0, (width - gutter - contentWidth) / 2)

    // Where time zero is drawn, counted from the left of the CONTENT — not from
    // the left of the pane.
    //
    // The centring used to be a left margin on the viewport, which made the strip
    // beside a short scene a place the timeline was not allowed into: flick, and
    // the clips slid under a black band and were clipped away by an edge that
    // looked like panel. The viewport is now the whole pane and the padding is
    // part of what scrolls, so the same gesture carries the clips across all of
    // it and nothing is eaten on the way.
    readonly property real pad: gutter + centrePad

    // Lent to the tab strip of whichever slot is showing this panel. A zoom
    // slider is chrome about the panel, not content in it: in the strip it costs
    // no height at all, and it stops covering the ruler it used to sit on.
    property Item stripControl: zoomBox

    // ── Zoom ──────────────────────────────────────────────────────────────
    // It used to have a strip of its own across the top, which cost 28 px of
    // every timeline forever to hold one slider you touch once a session. The
    // timeline is the panel whose height IS its usefulness — a lane you cannot
    // see is an element you forget — so the control floats in the corner
    // instead, quiet until you point at it, and Ctrl+wheel does the same job
    // without it.
    Rectangle {
        id: zoomBox
        z: 8
        width: zoomRow.width + 16
        height: 21
        radius: Theme.radiusSmall
        color: Theme.rail
        border.width: 1
        // Opaque, not translucent: a ruler mark showing through the control was
        // the ruler and the control both being half-readable.
        border.color: zoomHover.hovered ? Theme.inkFaint : Theme.edge

        Behavior on border.color { ColorAnimation { duration: Theme.motion(90) } }
        HoverHandler { id: zoomHover }

        Row {
            id: zoomRow
            anchors.centerIn: parent
            spacing: 6

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: Math.round(root.pxPerSecond) + " px/s"
                color: Theme.inkFaint
                font.family: Theme.mono
                font.pixelSize: 9
            }

            Slider {
                id: zoom
                anchors.verticalCenter: parent.verticalCenter
                width: 76
                // Sized explicitly: the Basic style's own implicit height is
                // taller than this strip, and the track is centred inside THAT,
                // which left it riding a few pixels above the label beside it.
                height: 14
                padding: 0
                // The whole of what is drawn, in the pane. `fitZoom` already
                // measures against `span`, which never goes below ten seconds —
                // so on a short scene this IS the ten-second view, and on a long
                // one it is the whole scene.
                from: Math.max(20, root.fitZoom)
                // Twice that at most: five seconds on screen and no further. A
                // value already past it — saved, or left over from a wider pane —
                // is pulled back by the Slider itself when the range moves.
                to: root.maxZoom > 0 ? Math.max(from, root.maxZoom) : Math.max(200, from * 4)
                value: Theme.pxPerSecond

                // The Basic style's slider is a pale bar with an oversized knob;
                // this one is the chrome's own: a thin rail that fills warm up to
                // where you are.
                background: Rectangle {
                    x: 0
                    y: zoom.availableHeight / 2 - height / 2
                    width: zoom.availableWidth
                    height: 3
                    radius: 2
                    color: Theme.sunk

                    Rectangle {
                        width: zoom.visualPosition * parent.width
                        height: parent.height
                        radius: 2
                        color: Theme.live
                    }
                }

                handle: Rectangle {
                    x: zoom.visualPosition * (zoom.availableWidth - width)
                    y: zoom.availableHeight / 2 - height / 2
                    width: 11; height: 11
                    radius: 6
                    color: zoom.pressed ? Theme.live : Theme.ink
                    border.color: Theme.sunk
                    border.width: 1
                }
            }
        }
    }

    // Nothing has been executed yet — or the scene is empty. Saying so is the
    // whole point of deleting the stand-in: an empty timeline that explains
    // itself beats a full one that is about someone else's video.
    Column {
        anchors.centerIn: parent
        spacing: 6
        visible: root.scene.elements.length === 0

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "nothing on the timeline"
            color: Theme.inkDim
            font.family: Theme.ui
            font.pixelSize: 12
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "⌘R runs the buffer — what it makes shows up here"
            color: Theme.inkFaint
            font.family: Theme.mono
            font.pixelSize: 11
        }
    }

    MouseArea {
        anchors.fill: parent
        onPressed: root.forceActiveFocus()
    }

    Flickable {
        id: flick
        visible: root.scene.elements.length > 0
        anchors {
            left: parent.left; right: parent.right
            top: parent.top; bottom: parent.bottom
        }
        // Time zero needs room to be a time and not a border — flush against the
        // panel's edge the playhead at 0 reads as an orange frame around the
        // pane, and its handle, drawn 5 px to its left, is clipped away — so the
        // room is inside the content, where it scrolls with everything else.
        contentWidth: root.pad + root.contentWidth
        // The lanes start BELOW the ruler, so the content is that much taller
        // than the lanes are: leaving the ruler out of the count made the last
        // lane unreachable — cut off by exactly the ruler's height, however far
        // you scrolled. The few pixels after it are so the bottom lane does not
        // sit flush against the panel's edge.
        contentHeight: lanes.height + ruler.height + 6
        flickableDirection: Flickable.HorizontalAndVerticalFlick
        clip: true

        ScrollBar.horizontal: ScrollBar {}
        ScrollBar.vertical: ScrollBar {}

        Column {
            id: lanes
            x: root.pad
            y: ruler.height
            spacing: 0

            Repeater {
                model: root.scene.elements

                Item {
                    id: lane
                    required property int index
                    required property var modelData
                    width: root.contentWidth

                    height: root.laneHeight

                    // A second's worth of grid, so a clip's edge can be read
                    // against the ruler without dragging the eye up to it.
                    Repeater {
                        model: Math.floor(root.span) + 1

                        Rectangle {
                            required property int index
                            x: index * root.pxPerSecond
                            width: 1
                            height: lane.height
                            color: Theme.edgeSoft
                        }
                    }

                    // Lit while something that needs an element is carried over
                    // it: the drop has a target, and the target says so.
                    Rectangle {
                        anchors.fill: parent
                        visible: root.hoverLane === lane.index
                        color: Qt.alpha(Theme.live, 0.10)
                        border.width: 1
                        border.color: Qt.alpha(Theme.live, 0.55)
                    }

                    Rectangle {
                        id: bar
                        x: (lane.modelData.l + bar.heldIn) * root.pxPerSecond
                        y: 5
                        width: Math.max(
                            (lane.modelData.d - bar.heldIn + bar.heldOut) * root.pxPerSecond - 2, 8)
                        // The LANE grows when it opens; the bar does not. It is
                        // still one clip, and a clip that swells to hold its own
                        // contents stops reading as a clip.
                        height: root.laneHeight - 10
                        radius: 4

                        readonly property bool away: root.openedName.length > 0
                                                     && root.openedName === lane.modelData.n

                        color: away ? "transparent" : Qt.alpha(Theme.kind[lane.modelData.kind], 0.30)
                        border.width: root.selectedIndex === lane.index ? 2 : 1
                        border.color: away
                                      ? Qt.rgba(1, 1, 1, 0.10)
                                      : (root.selectedIndex === lane.index
                                         ? Theme.live
                                         : Qt.rgba(1.000, 1.000, 1.000, 0.149))

                        // ── A fault the run found on this element ────────
                        // Hazard hatching, the mark every editing tool uses for
                        // "do not trust this yet". Diagonal because nothing else
                        // in a timeline runs diagonally: it cannot be mistaken
                        // for a clip, a waveform or a boundary, and it survives
                        // being drawn over any of them.
                        Item {
                            id: hazard
                            anchors.fill: parent
                            anchors.margins: 1
                            clip: true
                            visible: !bar.away
                                     && lane.modelData.flaws !== undefined
                                     && lane.modelData.flaws.length > 0

                            Repeater {
                                model: hazard.visible
                                       ? Math.ceil((hazard.width + hazard.height) / 14) : 0

                                Rectangle {
                                    required property int index
                                    width: 5
                                    height: hazard.height * 2
                                    x: index * 14 - hazard.height
                                    y: -hazard.height / 2
                                    rotation: -45
                                    color: Qt.alpha(Theme.flaw, 0.28)
                                }
                            }
                        }

                        // The waveform is one bar per tenth of a second, so each
                        // bar is exactly one snap step wide and the whole row
                        // reads as the same grid everything else is measured on.
                        Row {
                            id: wave
                            visible: !bar.away
                                     && (lane.modelData.kind === "video" || lane.modelData.kind === "sound")
                            anchors {
                                left: parent.left; right: parent.right
                                top: label.bottom; bottom: parent.bottom
                                leftMargin: 4; rightMargin: 4
                                topMargin: 3; bottomMargin: 4
                            }
                            spacing: 0

                            Repeater {
                                model: Math.max(Math.round(lane.modelData.d * 10), 1)

                                Item {
                                    required property int index
                                    // Divide the row the bars actually live in,
                                    // not the clip: measuring the clip and then
                                    // insetting the row by its own margins made
                                    // the waveform exactly those margins too
                                    // wide, so it ran out past the right edge.
                                    width: Math.max(wave.width / Math.max(Math.round(lane.modelData.d * 10), 1), 1)
                                    // `parent` is null while a delegate is being
                                    // built or torn down, and the model is
                                    // replaced wholesale on every run.
                                    height: wave.height

                                    Rectangle {
                                        anchors.centerIn: parent
                                        width: Math.max(parent.width - 1, 1)
                                        // Deterministic pseudo-waveform: it must
                                        // not reshuffle on every re-render.
                                        height: parent.height * (0.22 + 0.78 * Math.abs(
                                            Math.sin(parent.index * 0.7)
                                            * Math.cos(parent.index * 0.21)
                                            * Math.sin(parent.index * 0.05 + 1)))
                                        color: Qt.alpha(Theme.kind[lane.modelData.kind], 0.55)
                                    }
                                }
                            }
                        }

                        // The name sits on a band of its own along the top of
                        // the clip, the way every NLE that has to write over a
                        // waveform does it. Outlined text on top of the waveform
                        // was the alternative and it loses: an outline fights the
                        // very peaks it is drawn over, and the eye has to work
                        // out which pixels are letter and which are audio. A band
                        // gives the letters a floor, and it costs the waveform
                        // nothing — the waveform starts underneath it.
                        Rectangle {
                            id: label
                            visible: !bar.away
                            anchors { left: parent.left; right: parent.right; top: parent.top }
                            anchors.margins: 1
                            height: 16
                            topLeftRadius: 3
                            topRightRadius: 3
                            color: Qt.alpha(Theme.kind[lane.modelData.kind], 0.92)
                            clip: true

                            Row {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: 6
                                anchors.right: parent.right
                                anchors.rightMargin: 6
                                spacing: 5

                                // It breathes rather than blinks. A blink is a
                                // notification — something that just happened and
                                // wants answering; this is a state the scene is
                                // in, and it has to be able to sit there for an
                                // hour without becoming unbearable. The glyph
                                // scales, never the band: a row that changed
                                // height sixty times a second would move every
                                // clip under it.
                                Text {
                                    id: hazardMark
                                    visible: hazard.visible
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: "\u26A0"
                                    color: Theme.flaw
                                    font.pixelSize: 11
                                    transformOrigin: Item.Center

                                    SequentialAnimation on scale {
                                        running: hazardMark.visible
                                        loops: Animation.Infinite
                                        NumberAnimation {
                                            from: 1.0; to: 1.20
                                            duration: 460; easing.type: Easing.InOutSine
                                        }
                                        NumberAnimation {
                                            from: 1.20; to: 1.0
                                            duration: 460; easing.type: Easing.InOutSine
                                        }
                                    }
                                }

                                // Something animates this element, and clicking
                                // opens it. Effects are never drawn on the
                                // timeline itself: it stays a map of WHAT is on
                                // screen and WHEN.
                                Text {
                                    visible: lane.modelData.effects.length > 0
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: "▸"
                                    color: Qt.rgba(0, 0, 0, 0.55)
                                    font.pixelSize: 9
                                }

                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: lane.modelData.n
                                    // Near-black on a saturated band, which beats
                                    // white on every hue this palette uses.
                                    color: Qt.rgba(0.04, 0.06, 0.09, 0.92)
                                    font.family: Theme.ui
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                }
                            }
                        }

                        // ── The edge you can pull ─────────────────────────
                        // A clip that can only be opened is a label; the first
                        // gesture any editor has is dragging where something
                        // stops. Held in seconds while the drag lasts, written
                        // once on release — the buffer is not rewritten sixty
                        // times a second.
                        //
                        // The right edge only. Where a clip STARTS is where the
                        // lines above it left the clock — `waitFor`, `flush`,
                        // a `wait` — and that is a statement to move, not an
                        // argument to change. A handle that could only refuse
                        // is a handle that lies about what it does.
                        property real heldIn: 0
                        property real heldOut: 0

                        Repeater {
                            model: [{ edge: "out", at: 1 }]

                            MouseArea {
                                required property var modelData
                                readonly property bool outward: modelData.edge === "out"

                                x: outward ? bar.width - 9 : 0
                                width: 9
                                height: bar.height
                                hoverEnabled: true
                                cursorShape: Qt.SizeHorCursor
                                preventStealing: true
                                visible: !bar.away

                                property real anchorX: 0
                                property bool moved: false

                                onPressed: (mouse) => {
                                    root.forceActiveFocus();
                                    anchorX = mapToItem(lane, mouse.x, 0).x;
                                    moved = false;
                                }

                                onPositionChanged: (mouse) => {
                                    if (!pressed)
                                        return;
                                    const now = mapToItem(lane, mouse.x, 0).x;
                                    const free = (mouse.modifiers & Qt.ControlModifier) !== 0;
                                    // The EDGE is what snaps, not the distance it
                                    // travelled: lining a clip up with the one
                                    // above it is the whole point, and a snapped
                                    // delta only ever lines up with where the
                                    // drag started.
                                    const edge = lane.modelData.l + lane.modelData.d;
                                    const delta = root.snapped(edge + (now - anchorX) / root.pxPerSecond, free) - edge;
                                    if (Math.abs(delta) > 0.001)
                                        moved = true;

                                    // Neither edge may pass the other: a clip of
                                    // no length is a clip you can no longer find.
                                    if (outward)
                                        bar.heldOut = Math.max(0.1 - lane.modelData.d, delta);
                                    else
                                        bar.heldIn = Math.min(lane.modelData.d - 0.1, delta);
                                }

                                onReleased: {
                                    if (moved) {
                                        const at = outward
                                                 ? lane.modelData.l + lane.modelData.d + bar.heldOut
                                                 : lane.modelData.l + bar.heldIn;
                                        root.trimmed(lane.modelData, modelData.edge, at);
                                    }
                                    bar.heldIn = 0;
                                    bar.heldOut = 0;
                                }

                                // The edge, drawn only when the pointer is on it
                                // or pulling it.
                                Rectangle {
                                    anchors {
                                        right: parent.outward ? parent.right : undefined
                                        left: parent.outward ? undefined : parent.left
                                        top: parent.top; bottom: parent.bottom
                                        topMargin: 3; bottomMargin: 3
                                    }
                                    width: 3
                                    radius: 1.5
                                    color: Theme.kind[lane.modelData.kind]
                                    opacity: parent.containsMouse || parent.pressed ? 0.95 : 0
                                    Behavior on opacity { NumberAnimation { duration: Theme.motion(90) } }
                                }
                            }
                        }

                        // A tap opens the element — somewhere else.
                        //
                        // What is inside a clip does not belong on the timeline:
                        // rows that grow push everything below them down, and a
                        // timeline whose geometry changes when you look at
                        // something has stopped being a map. The bar reports
                        // where it is on screen so the card can start there and
                        // travel, which is what makes it obvious that the big
                        // thing in the middle IS this clip.
                        TapHandler {
                            onTapped: {
                                root.forceActiveFocus();
                                const at = bar.mapToItem(null, 0, 0);
                                root.elementOpened(
                                    lane.modelData,
                                    Qt.rect(at.x, at.y, bar.width, bar.height)
                                );
                            }
                        }
                    }
                }
            }
        }

        // Sticky: the ruler scrolls with the lanes horizontally but never leaves
        // the top, because a time reading you have to scroll to is not a reading.
        Rectangle {
            id: ruler
            x: root.pad
            y: flick.contentY
            width: root.contentWidth
            height: 28
            z: 5
            color: Theme.rail

            Repeater {
                model: Math.floor(root.span) + 1

                Item {
                    required property int index
                    x: index * root.pxPerSecond
                    width: root.pxPerSecond
                    height: ruler.height

                    // The tick stops short of its own number. Now that the
                    // figure sits ON the line, a full-height tick would run up
                    // through the digits and read as a strikethrough; it only has
                    // to reach far enough down to meet the lanes below.
                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: 1
                        height: 6
                        color: parent.index % 2 ? Theme.edgeSoft : Theme.edge
                    }

                    Text {
                        id: stamp
                        visible: parent.index % 2 === 0
                        // Centred on the line it names, not parked beside it: a
                        // number to the right of its tick reads as belonging to
                        // the space AFTER that second, and the colon of "00:00"
                        // sits over time zero. The clamp is the guard for a
                        // gutter too narrow to hold half a stamp — it should not
                        // bite at the shipped one.
                        x: parent.index === 0
                           ? Math.max(-stamp.implicitWidth / 2, -root.pad + 2)
                           : -stamp.implicitWidth / 2
                        anchors.verticalCenter: parent.verticalCenter
                        text: {
                            const m = Math.floor(parent.index / 60);
                            const s = parent.index % 60;
                            return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
                        }
                        color: Theme.inkFaint
                        font.family: Theme.mono
                        font.pixelSize: 11
                    }
                }
            }

            Rectangle {
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                height: 1
                color: Theme.edge
            }

            // Scrubbing. On the ruler only, and not over the lanes: a click on a
            // clip means "open this", and a surface where the same gesture does
            // two things depending on where it lands is a surface you stop
            // trusting. Drag included — a playhead you can only place, never
            // pull, is a slider with no handle.
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                preventStealing: true
                onPressed: (mouse) => {
                    // Scrubbing is working in the timeline: the caret leaves the
                    // code pane, and Space stops being a space.
                    root.forceActiveFocus();
                    root.scrubbed(mouse.x / root.pxPerSecond);
                }
                onPositionChanged: (mouse) => {
                    if (pressed)
                        root.scrubbed(mouse.x / root.pxPerSecond);
                }
            }
        }

        // Where a carried template would land.
        Item {
            visible: root.dropAt >= 0
            x: root.pad + root.dropAt * root.pxPerSecond
            y: flick.contentY
            width: 1
            height: flick.height
            z: 6

            Rectangle {
                anchors.fill: parent
                color: Theme.live
            }

            Rectangle {
                anchors { bottom: parent.top; bottomMargin: -18; horizontalCenter: parent.horizontalCenter }
                width: dropStamp.implicitWidth + 12
                height: 18
                radius: 3
                color: Theme.live

                Text {
                    id: dropStamp
                    anchors.centerIn: parent
                    text: root.dropAt.toFixed(1) + "s"
                    color: "#0b1018"
                    font.family: Theme.mono
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                }
            }
        }

        // ── The range ─────────────────────────────────────────────────────
        // Everything outside it, quietened. Not hidden and not greyed to
        // nothing: the rest of the scene is still there and you still have to
        // be able to read it — it is simply not what you are working on.
        Repeater {
            model: root.ranged ? [{ from: 0, to: root.markIn }, { from: root.markOut, to: root.scene.duration }] : []

            Rectangle {
                required property var modelData
                visible: modelData.to > modelData.from
                x: root.pad + modelData.from * root.pxPerSecond
                y: flick.contentY
                width: Math.max((modelData.to - modelData.from) * root.pxPerSecond, 0)
                height: flick.height
                z: 3
                color: Qt.rgba(0.02, 0.027, 0.039, 0.55)
            }
        }

        // The two edges of it, and their handles on the ruler.
        Repeater {
            model: root.ranged ? [{ at: root.markIn, tip: "in" }, { at: root.markOut, tip: "out" }] : []

            Item {
                required property var modelData
                x: root.pad + modelData.at * root.pxPerSecond
                y: flick.contentY
                width: 1
                height: flick.height
                z: 6

                Rectangle {
                    anchors.fill: parent
                    color: Theme.ok
                }

                Rectangle {
                    y: 6
                    x: parent.modelData.tip === "in" ? 0 : -13
                    width: 13
                    height: 13
                    color: Theme.ok
                    topLeftRadius: parent.modelData.tip === "in" ? 3 : 0
                    bottomLeftRadius: parent.modelData.tip === "in" ? 3 : 0
                    topRightRadius: parent.modelData.tip === "in" ? 0 : 3
                    bottomRightRadius: parent.modelData.tip === "in" ? 0 : 3

                    Text {
                        anchors.centerIn: parent
                        text: parent.parent.modelData.tip === "in" ? "I" : "O"
                        color: "#04170e"
                        font.family: Theme.mono
                        font.pixelSize: 9
                        font.weight: Font.DemiBold
                    }
                }
            }
        }

        // ── Where the scene's time joins ──────────────────────────────────
        // Every `wait()` in the code, drawn across every lane.
        //
        // It is the one place the language lets a change propagate: what is
        // before a wait has ended, what is after starts from it. So lengthening
        // an animation pushes what follows exactly when one of these lines sits
        // between them — the timeline does not invent a rule about rippling, it
        // shows the one the scene already has.
        //
        // The gap the wait leaves is drawn as well as the join: `wait(0.5)` is
        // half a second in which nothing is scheduled, and a bare line would say
        // it was instantaneous.
        //
        // The gap is painted UNDER the lanes, not over them. Over them it had
        // to be faint enough to leave a clip's name readable through it, and at
        // 10% it was faint enough to miss altogether. On the ground it can be
        // twice as strong and cover nothing: a bar is 30% of its hue, so the
        // wait shows through it as a warmer bar, and the name band at 92% is
        // simply on top. What still crosses the lanes is the join line, the
        // stamp, and the clocks — all of them thin or see-through.
        Repeater {
            model: root.scene.waits !== undefined ? root.scene.waits : []

            Rectangle {
                required property var modelData
                x: root.pad + modelData.at * root.pxPerSecond
                y: flick.contentY
                width: modelData.d * root.pxPerSecond
                height: flick.height
                z: -1
                color: Qt.rgba(0.878, 0.376, 0.361, 0.20)
            }
        }

        Repeater {
            model: root.scene.waits !== undefined ? root.scene.waits : []

            Item {
                id: join
                required property var modelData
                x: root.pad + modelData.at * root.pxPerSecond
                y: flick.contentY
                width: Math.max(modelData.d * root.pxPerSecond, 1)
                height: flick.height
                z: 4

                // The join, on the instant everything before it ended.
                Rectangle {
                    width: 1
                    height: parent.height
                    color: Qt.rgba(0.878, 0.376, 0.361, 0.55)
                }

                // And where it is written, so the line is a thing you can go to
                // rather than a mark you have to decode.
                // At the FOOT of the pane, not at its head: the head is the
                // ruler's and the space under the last lane is the only place a
                // label can sit without landing on a clip and becoming dark red
                // text on a green bar.
                //
                // And it is the gap's own value, so clicking it edits the line
                // that wrote it: `wait(0.3)` is one number in one call, which is
                // the smallest edit this timeline can make.
                Rectangle {
                    id: gapStamp
                    x: 4
                    y: join.height - height - 4
                    width: stampText.implicitWidth + 12
                    height: stampText.implicitHeight + 6
                    radius: 3
                    // Always on a ground of its own. The stamp sits at the foot
                    // of the pane, where a lane, the grid or a clip can pass
                    // behind it, and dark red on green is not a reading — a
                    // chip at 92% settles what it is written on. Not a backdrop
                    // blur: that is a ShaderEffectSource and a pass per stamp
                    // for the same answer.
                    color: editing || stampMouse.containsMouse
                           ? Qt.rgba(0.153, 0.086, 0.086, 0.94)
                           : Qt.alpha(Theme.sunk, 0.92)
                    border.width: 1
                    border.color: editing
                                  ? Qt.rgba(0.878, 0.376, 0.361, 0.8)
                                  : Qt.rgba(0.878, 0.376, 0.361, 0.22)
                    visible: join.width > width + 6

                    readonly property bool editing: root.editingWait === join.modelData.line

                    Text {
                        id: stampText
                        anchors.centerIn: parent
                        visible: !gapStamp.editing
                        text: "wait " + join.modelData.says.toFixed(1) + "s"
                        color: Qt.rgba(0.945, 0.541, 0.525, 1)
                        font.family: Theme.mono
                        font.pixelSize: 10
                    }

                    TextInput {
                        id: stampEntry
                        anchors { fill: parent; leftMargin: 6; rightMargin: 6 }
                        verticalAlignment: TextInput.AlignVCenter
                        visible: gapStamp.editing
                        color: Qt.rgba(0.945, 0.541, 0.525, 1)
                        font.family: Theme.mono
                        font.pixelSize: 10
                        selectByMouse: true

                        onAccepted: {
                            root.waitChanged(join.modelData.line, stampEntry.text.trim());
                            root.editingWait = -1;
                        }
                        Keys.onEscapePressed: root.editingWait = -1;
                        onActiveFocusChanged: if (!activeFocus && gapStamp.editing) root.editingWait = -1;
                    }

                    MouseArea {
                        id: stampMouse
                        anchors.fill: parent
                        anchors.margins: -3
                        hoverEnabled: true
                        enabled: !gapStamp.editing
                        cursorShape: Qt.IBeamCursor
                        onClicked: {
                            root.editingWait = join.modelData.line;
                            // The number alone, not the sentence: what you are
                            // editing is the argument in the call.
                            stampEntry.text = join.modelData.says.toFixed(2);
                            stampEntry.forceActiveFocus();
                            stampEntry.selectAll();
                        }
                    }
                }

                // ── Clocks, rising ────────────────────────────────────────
                // Two or three small clocks drift up the gap, faint, and gone
                // by the ruler: the band is a pause, and this is what says so
                // from across the room, before the stamp is read. Their hands
                // do not turn — a pause is exactly a clock whose hands are
                // still.
                //
                // Circles and two lines, no image and no shader: the band is
                // the picture, these are a hint laid over it, and they must
                // lose to a clip's name every time they cross one — half
                // opacity at their brightest, one pixel of stroke.
                //
                // None at all when they cannot be seen: while the band is
                // scrolled out of the pane, while it is too narrow to hold one,
                // and when the system asked for less movement — a still clock
                // sitting on a clip for an hour is not a quieter version of
                // this, it is a smudge.
                Repeater {
                    id: clocks
                    model: !Theme.reducedMotion
                           && join.x < flick.contentX + flick.width
                           && join.x + join.width > flick.contentX
                           ? Math.min(3, Math.floor(join.width / 20)) : 0

                    Item {
                        id: clock
                        required property int index
                        width: 14
                        height: 14
                        x: (index + 0.5) * join.width / clocks.count - width / 2

                        // 0 at the foot of the pane, 1 just under the ruler.
                        property real climb: 0
                        readonly property real foot: join.height - 26
                        readonly property real head: ruler.height + 6
                        y: foot - climb * (foot - head)
                        opacity: Math.sin(climb * Math.PI) * 0.5

                        Rectangle {
                            anchors.fill: parent
                            radius: width / 2
                            color: "transparent"
                            border.width: 1
                            border.color: Qt.rgba(0.878, 0.376, 0.361, 1)
                        }

                        Rectangle {
                            x: parent.width / 2 - 0.5
                            y: 3
                            width: 1
                            height: parent.height / 2 - 3
                            color: Qt.rgba(0.878, 0.376, 0.361, 1)
                        }

                        Rectangle {
                            x: parent.width / 2
                            y: parent.height / 2 - 0.5
                            width: parent.width / 2 - 3
                            height: 1
                            color: Qt.rgba(0.878, 0.376, 0.361, 1)
                        }

                        // Each starts later and climbs slower than the one
                        // before it, so they never line up into a row — a row
                        // is a pattern, and a pattern is something to read.
                        SequentialAnimation on climb {
                            running: true
                            PauseAnimation { duration: clock.index * 2100 }
                            NumberAnimation {
                                from: 0; to: 1
                                duration: 6000 + clock.index * 900
                                loops: Animation.Infinite
                            }
                        }
                    }
                }
            }
        }

        // Drawn over every lane AND over the ruler: the playhead is the most
        // urgent thing on screen and never hides behind anything.
        Item {
            x: root.pad + root.playhead * root.pxPerSecond
            y: flick.contentY
            width: 1
            height: flick.height
            z: 6

            Rectangle {
                anchors.fill: parent
                color: Theme.live
            }

            // The grab handle, which is also what makes the line findable when it
            // sits over a bright clip.
            Canvas {
                width: 11; height: 7
                x: -5
                onPaint: {
                    const ctx = getContext("2d");
                    ctx.reset();
                    ctx.fillStyle = Theme.live;
                    ctx.beginPath();
                    ctx.moveTo(0, 0);
                    ctx.lineTo(width, 0);
                    ctx.lineTo(width / 2, height);
                    ctx.closePath();
                    ctx.fill();
                }
            }
        }
    }
}
