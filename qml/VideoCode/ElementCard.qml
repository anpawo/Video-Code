// One element of the scene, opened.
//
// The CLIP travels — not a card shaped like it.
//
// The bar you clicked leaves its lane, grows, and comes to rest in the middle of
// the window; the card is built around it once it lands. That distinction is the
// whole point: a panel that merely starts at the clip's rectangle is a second
// object appearing over a first one that never moved, and the eye has two things
// to reconcile. Here there is one thing, and it went somewhere. Its lane stays
// exactly as it was, with a hollow where the bar used to be, so the timeline
// does not reflow and you can see where it will go back.
//
// What is inside a clip does not belong on the timeline. Rows that grow push
// everything below them down, and a map whose geometry changes when you look at
// something has stopped being a map. So the effects live here, under the clip
// they belong to, drawn against the CLIP's own length rather than the scene's:
// at timeline scale a two-second clip is a sliver and a 0.4 s fade is a sliver
// of a sliver, while here that fade is a fifth of what you are looking at.
//
// The ruler under the block is what makes the spans mean anything — without it
// they are proportions of nothing — and the same half-second and whole-second
// lines carry down through the effect rows, so a bar is read AGAINST the ruler
// instead of near it.
//
// A row made of several inputs from one line — `Text("GRADIENT")` is one per
// glyph — opens into its members instead, and each member opens into its own
// card. Same gesture, same question: what is really in there.
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls

Item {
    id: root
    anchors.fill: parent
    visible: element !== null

    property var element: null
    property var effectNames: []

    // Where the clip is on screen, so the card can start from it.
    property rect from: Qt.rect(0, 0, 0, 0)

    // The scene's text, so the card can read what the line actually says. Bound
    // rather than fetched: a gesture rewrites the buffer and every field on the
    // card has to agree with it on the next frame.
    property string buffer: ""

    signal closed()
    // One value, on the call that made this element. The shell writes it and
    // re-runs the scene; the card never edits the buffer itself.
    signal argumentWritten(var element, string call, string name, string value)
    signal jumpRequested(var element)
    signal effectRequested(var element, var effect, var options)
    signal memberOpened(var member, rect where)
    // An applied effect, acted on through the call that wrote it.
    signal effectRemoved(var fx)
    signal effectWritten(var fx, string name, string value)
    signal effectJumped(var fx)
    // Off, or back on: the line is commented out rather than deleted.
    signal effectToggled(int line, bool off)

    readonly property var members: element !== null && element.members !== undefined
                                   ? element.members : []
    readonly property var effects: element !== null && element.effects !== undefined
                                   ? element.effects : []
    // Statements about this element that are commented out.
    //
    // They are not in the scene — nothing ran — so they cannot come from it.
    // They come from the BUFFER, which is where they still are: `# square.fadeIn()`
    // is an effect that exists, in order, with its arguments, and is switched
    // off. A card that showed only what ran would be a card you cannot switch
    // anything back on from.
    readonly property var silenced: {
        if (element === null || members.length > 0 || element.n === undefined)
            return [];

        const out = [];
        const lines = buffer.split("\n");
        const head = element.n + ".";
        for (let i = 0; i < lines.length; i++) {
            const parts = /^\s*#\s?(.*)$/.exec(lines[i]);
            if (parts === null)
                continue;
            const body = parts[1].trim();
            if (body.indexOf(head) !== 0)
                continue;
            const call = /^[A-Za-z_]\w*\.([A-Za-z_]\w*)/.exec(body);
            out.push({
                n: call !== null ? call[1] : body, line: i + 1, off: true,
                said: body, l: 0, d: 0, call: call !== null ? call[1] : "", kinds: []
            });
        }
        return out;
    }

    // Read top-down as a timeline: the effect that starts first is the one at
    // the top. Ties on the start go to the SHORTER one, which puts an instant
    // `opacity` above the `fadeIn` that begins alongside it — the short bar
    // would otherwise be buried under a long one it does not belong inside.
    //
    // `slice()` because `sort` works in place and `effects` is a binding, and
    // the commented-out statements stay together at the end: they never ran, so
    // they have no start to be sorted by.
    readonly property var rows: {
        if (members.length > 0)
            return members;
        const played = effects.slice().sort(function (a, b) {
            return a.l !== b.l ? a.l - b.l : a.d - b.d;
        });
        return played.concat(silenced);
    }

    // The clip's own extent, which is what the bars below are measured against.
    readonly property real span: element !== null && element.d > 0 ? element.d : 1
    readonly property real origin: element !== null ? element.l : 0

    readonly property string kind: element !== null && element.kind !== undefined
                                   ? element.kind : "video"
    readonly property color hue: Theme.kind[kind] !== undefined ? Theme.kind[kind] : Theme.inkDim
    // The host's complement, shared by everything that animates it: one hue for
    // the thing, one for what happens to it.
    readonly property color fxHue: Theme.fxKind[kind] !== undefined ? Theme.fxKind[kind] : Theme.live

    readonly property var kindLabel: ({
        "video": "Video", "sound": "Sound", "image": "Image",
        "subs": "Subtitles", "polygon": "Polygon"
    })

    // 0 = still in its lane, 1 = landed in the middle. Everything the flight
    // touches is derived from it, so there is one clock for the whole gesture
    // rather than four animations that can disagree about where the bar is.
    property real travel: 0

    Behavior on travel {
        NumberAnimation { duration: Theme.motion(220); easing.type: Easing.OutCubic }
    }

    function open(what, where) {
        // Clicking a second clip while the first is on its way home: the return
        // trip's timer is still armed and would clear the element under the card
        // that has just opened.
        landing.stop();

        element = what;
        from = where;
        library = false;
        travel = 0;
        // One frame at zero before it is told to go: setting both in the same
        // tick means no journey to animate.
        launch.start();
    }

    // A gesture rewrote the scene, and the card is a VIEW of it: the bars have
    // to become the ones that came back, not the ones the card opened with.
    // Matched by the element's index rather than by its place in the list — a
    // deleted effect can change the order of neither, but a deleted element can.
    function rebind(elements) {
        if (element === null || element.index === undefined)
            return;

        for (const one of elements) {
            if (one.index === element.index && one.n === element.n) {
                element = one;
                return;
            }
            for (const member of (one.members !== undefined ? one.members : [])) {
                if (member.index === element.index && member.n === element.n) {
                    element = member;
                    return;
                }
            }
        }

        // Its element is gone from the scene — deleted, or renamed into
        // something else. A card describing nothing is worse than no card.
        close();
    }

    function close() {
        // And the other way round, for a card shut inside the frame it opened on.
        launch.stop();

        root.closed();
        travel = 0;
        // The element is kept until the bar is home — it is what the lane's
        // hollow and the flying bar are both drawn from.
        landing.start();
    }

    Timer {
        id: launch
        interval: 16
        onTriggered: root.travel = 1
    }

    Timer {
        id: landing
        interval: Theme.motion(230)
        onTriggered: root.element = null
    }

    // The effects library, summoned with E. Not a permanent neighbour of the
    // card: it is called for, used, dismissed — so it spends no layout on being
    // absent.
    property bool library: false

    // ── Placing an effect: choose it, set it up, then aim it ──────────────
    // The three are one gesture and they happen in that order for a reason. An
    // effect's DURATION is what you are about to drop — a 0.4 s fade is a fifth
    // of a two-second clip, a whole third of a 1.2 s one — so the parameters are
    // set first and the bar you drag is the size it will be. Choosing the moment
    // before the length would mean aiming at something whose shape you cannot
    // see yet, and correcting it afterwards by hand.
    property var picked: null
    // name → what will be written for it. Seeded from the signature's own
    // defaults, so an untouched field writes nothing at all.
    property var values: ({})

    property bool dragging: false
    // Where the drop would land, in seconds from the start of the ELEMENT, and
    // whether it is snapped there or sitting exactly under the pointer.
    property real dropAt: 0
    property bool exact: false

    // The tenth of a second is the trim resolution everywhere else in this
    // window — the timeline's own ruler is drawn in tenths — so a drop lands on
    // one unless you say otherwise.
    readonly property real snap: 0.1

    function pick(effect) {
        const seeded = ({});
        for (const parameter of effect.params)
            seeded[parameter.name] = parameter.value;
        values = seeded;
        picked = effect;
        dropAt = 0;
    }

    function unpick() {
        picked = null;
        dragging = false;
        // Back from the fields: the card answers keys again, which is what makes
        // Escape and E work straight after setting an effect up.
        forceActiveFocus();
    }

    // How long the effect being placed will last, read off its own fields: the
    // one number that decides the width of what you are dragging.
    readonly property real pickedDuration: {
        if (picked === null)
            return 0;
        const written = values["duration"];
        const seconds = written === undefined ? NaN : parseFloat(written);
        // No `duration` in the signature, or a value that is not a number yet
        // while it is being typed: a single frame, which is what an effect with
        // no length of its own covers.
        return isNaN(seconds) || seconds <= 0 ? 1 / 30 : seconds;
    }

    // Every field the effect takes that has no default. Until they are filled,
    // the call would not run, so the drop is refused rather than written.
    readonly property var missing: {
        if (picked === null)
            return [];
        const out = [];
        for (const parameter of picked.params) {
            const written = values[parameter.name];
            if (parameter.value.length === 0 && (written === undefined || written.trim().length === 0))
                out.push(parameter.name);
        }
        return out;
    }

    // ── The element's own line, as fields ─────────────────────────────────
    // What the call that made this element takes, straight from its signature —
    // `Square` answers side, fillColor, stroke…, `Video` answers startFrame,
    // endFrame, cuts. Nothing here knows what a video is; the class does.
    readonly property string cls: element !== null && element.cls !== undefined ? element.cls : ""
    readonly property var arguments: cls.length > 0 ? Shell.inputParams(cls) : []

    // Whether the line is one this card can safely write to. An element built in
    // a loop, or by a helper, has a line that says where it came from but not a
    // call anyone can rewrite — better to show the values and refuse the edit
    // than to write into the wrong place.
    readonly property bool writable: element !== null
                                     && element.line !== undefined && element.line > 0
                                     && cls.length > 0
                                     && Shell.callsOnLine(buffer, element.line).indexOf(cls) >= 0

    function written(name) {
        if (!writable)
            return "";
        return Shell.readArgument(buffer, element.line, cls, name);
    }

    // Turn a pointer position into a moment on the element.
    function timeAt(globalX) {
        const at = bar.mapFromItem(null, globalX, 0);
        const seconds = Math.max(0, Math.min(root.span, at.x / Math.max(bar.width, 1) * root.span));
        return root.exact ? seconds : Math.round(seconds / root.snap) * root.snap;
    }

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0.02, 0.027, 0.039, 0.88)
        opacity: root.travel

        MouseArea {
            anchors.fill: parent
            onClicked: root.close()
        }
    }

    Rectangle {
        id: card

        readonly property int pad: 18
        readonly property int wide: Math.min(1080, root.width - 48)
        readonly property int rowsTall: Math.max(root.rows.length * 42 + Math.max(root.rows.length - 1, 0) * 7, 28)
        readonly property int fieldsTall: root.arguments.length > 0 ? 32 : 0
        readonly property int tall: Math.min(pad + 22 + 76 + 8 + 24 + 12 + rowsTall + fieldsTall + 34 + pad,
                                             root.height - 48)

        // The card does not travel — the bar does. It is at its final size and
        // place from the first frame, and simply arrives: everything in it has
        // nowhere to come from, and a box that grows behind a moving bar is a
        // second thing to watch.
        x: (root.width - wide) / 2
        y: Math.min(Math.max(24, root.height * 0.12), Math.max(24, root.height - tall - 24))
        width: wide
        height: tall

        // Behind the bar until the bar is nearly home. The delay is what makes
        // the eye follow one moving thing: the chrome shows up around a bar that
        // has already stopped.
        opacity: Math.max(0, (root.travel - 0.55) / 0.45)

        clip: true
        color: Theme.panel
        radius: Theme.radius
        border.width: 1
        border.color: Theme.edge

        MouseArea { anchors.fill: parent }

        // ── What it is ────────────────────────────────────────────────────
        Item {
            id: head
            anchors { left: parent.left; right: parent.right; top: parent.top }
            anchors.margins: card.pad
            height: 12

            Rectangle {
                id: glyph
                anchors.verticalCenter: parent.verticalCenter
                width: 9; height: 9
                radius: 2
                color: root.hue
            }

            Text {
                anchors { left: glyph.right; leftMargin: 8; verticalCenter: parent.verticalCenter }
                text: root.kindLabel[root.kind] !== undefined
                      ? root.kindLabel[root.kind].toUpperCase() : root.kind.toUpperCase()
                color: Theme.inkFaint
                font.family: Theme.ui
                font.pixelSize: 11
                font.weight: Font.DemiBold
                font.letterSpacing: 1.1
            }

            // Where it was written. The card is the one surface that can afford
            // to say it, and clicking it puts the caret there.
            Text {
                id: where
                anchors { right: dur.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
                text: root.element !== null && root.element.line > 0
                      ? "line " + root.element.line : ""
                color: jump.containsMouse ? Theme.live : Theme.inkFaint
                font.family: Theme.mono
                font.pixelSize: 11

                MouseArea {
                    id: jump
                    anchors.fill: parent
                    anchors.margins: -6
                    hoverEnabled: true
                    onClicked: root.jumpRequested(root.element)
                }
            }

            Text {
                id: dur
                anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                text: root.span.toFixed(1) + "s"
                color: Theme.inkDim
                font.family: Theme.mono
                font.pixelSize: 12
            }
        }

        // ── The element itself, re-scaled to the whole width ──────────────
        // Shown only once the flight is over: until then this exact rectangle is
        // being drawn by the bar that is still on its way here, and two of them
        // would be one too many. The swap happens at rest, where nothing moves.
        Rectangle {
            id: bar
            visible: root.travel >= 1
            anchors {
                left: parent.left; right: parent.right
                leftMargin: card.pad; rightMargin: card.pad
                top: head.bottom; topMargin: 10
            }
            height: 76
            radius: 6
            color: root.hue
            border.width: 1
            border.color: Qt.rgba(1, 1, 1, 0.18)
            clip: true

            // Same problem as the timeline clips, one size up: the waveform runs
            // straight under the name, so the glyphs are stroked to keep their
            // weight against it.
            Row {
                anchors { fill: parent; topMargin: 10; bottomMargin: 10 }
                spacing: 1
                visible: root.kind === "video" || root.kind === "sound"
                opacity: 0.34

                Repeater {
                    model: Math.max(Math.round(root.span * 10), 1)

                    Rectangle {
                        required property int index
                        // Deterministic pseudo-waveform: it must not reshuffle
                        // every time the card is opened.
                        readonly property real v: 22 + 78 * Math.abs(
                            Math.sin(index * 0.7) * Math.cos(index * 0.21) * Math.sin(index * 0.05 + 1))
                        width: Math.max((bar.width - 20) / Math.max(Math.round(root.span * 10), 1) - 1, 1)
                        height: parent.height * v / 100
                        anchors.verticalCenter: parent.verticalCenter
                        radius: 1
                        color: "#dff3ee"
                    }
                }
            }

            Text {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                text: root.element !== null ? root.element.n : ""
                color: "#eef3f9"
                font.family: Theme.ui
                font.pixelSize: 15
                font.weight: Font.DemiBold
                style: Text.Outline
                styleColor: Qt.rgba(0.043, 0.055, 0.075, 0.85)
            }

            // What the drop would cover, drawn ON the element while you aim it.
            // The width is the effect's own duration against the element's, so
            // the thing you are placing is the size it will be — a fade that
            // covers a third of the clip looks like a third before it exists.
            Rectangle {
                id: ghost
                visible: root.dragging
                x: bar.width * root.dropAt / root.span
                width: Math.max(bar.width * root.pickedDuration / root.span, 3)
                anchors { top: parent.top; bottom: parent.bottom }
                color: Qt.alpha(root.fxHue, 0.55)
                border.width: 1
                border.color: root.fxHue
                radius: 4
            }

            // The instant it lands on. Green when it is exactly under the
            // pointer, accent when it snapped — you can see WHICH you got
            // without being told, which is the only way a modifier key is ever
            // learned.
            Rectangle {
                visible: root.dragging
                x: bar.width * root.dropAt / root.span
                width: 2
                anchors { top: parent.top; bottom: parent.bottom }
                color: root.exact ? Theme.ok : Theme.live
                z: 2

                Rectangle {
                    y: 6
                    x: 6
                    width: stamp.implicitWidth + 12
                    height: stamp.implicitHeight + 6
                    radius: 3
                    color: root.exact ? Theme.ok : Theme.live

                    Text {
                        id: stamp
                        anchors.centerIn: parent
                        text: root.dropAt.toFixed(2) + "s → " + (root.dropAt + root.pickedDuration).toFixed(2) + "s"
                        color: root.exact ? "#04170e" : "#180c06"
                        font.family: Theme.mono
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                    }
                }
            }
        }

        // ── The element's own duration, laid out under it ─────────────────
        Item {
            id: scale
            anchors {
                left: bar.left; right: bar.right
                top: bar.bottom; topMargin: 8
            }
            height: 24

            Rectangle {
                anchors { left: parent.left; right: parent.right; top: parent.top }
                height: 1
                color: Theme.edge
            }

            // A tick is a time and a class: the tenth is the trim resolution and
            // stays nearly silent, the half second is warm, the whole second is
            // the one you count in — and only whole seconds are ever labelled.
            readonly property var ticks: {
                const d = root.span;
                const every = d <= 8 ? 1 : (d <= 20 ? 2 : 5);
                const out = [];
                if (d <= 15) {
                    for (let n = 1; n * 0.1 < d; n++) {
                        if (n % 5 === 0)
                            continue;
                        out.push({ at: n * 0.1 / d, h: 4, c: Theme.edge, label: "" });
                    }
                }
                for (let h = 1; h * 0.5 < d; h++) {
                    if (h % 2 === 0)
                        continue;
                    out.push({ at: h * 0.5 / d, h: 8, c: "#88d9a94e", label: "" });
                }
                for (let t = 0; t <= d + 1e-6; t++)
                    out.push({ at: t / d, h: 12, c: "#cc4a86c5",
                               label: t % every === 0 ? t + "s" : "" });
                return out;
            }

            Repeater {
                model: scale.ticks

                Item {
                    required property var modelData
                    x: scale.width * modelData.at
                    y: 0
                    width: 1
                    height: scale.height

                    Rectangle {
                        id: stem
                        width: 1
                        height: parent.modelData.h
                        color: parent.modelData.c
                    }

                    Text {
                        anchors { top: stem.bottom; topMargin: 2; horizontalCenter: parent.horizontalCenter }
                        text: parent.modelData.label
                        color: Theme.inkFaint
                        font.family: Theme.mono
                        font.pixelSize: 10
                    }
                }
            }

            // The end of the element, named rather than counted: the last whole
            // second is not where a clip stops.
            Rectangle {
                x: scale.width - 1
                width: 1
                height: 12
                color: Theme.inkFaint

                Text {
                    anchors { top: parent.bottom; topMargin: 2; right: parent.right }
                    text: root.span.toFixed(1) + "s"
                    color: Theme.inkDim
                    font.family: Theme.mono
                    font.pixelSize: 10
                }
            }
        }

        // ── What animates it, on the element's own axis ───────────────────
        Item {
            id: applied
            anchors {
                left: bar.left; right: bar.right
                top: scale.bottom; topMargin: 12
                bottom: argRow.top; bottomMargin: 10
            }

            // The ruler's half-second and whole-second lines, carried down
            // behind the rows.
            Repeater {
                model: {
                    const out = [];
                    for (let h = 1; h * 0.5 < root.span; h++)
                        out.push({ at: h * 0.5 / root.span, c: h % 2 ? "#1fd9a94e" : "#334a86c5" });
                    return out;
                }

                Rectangle {
                    required property var modelData
                    x: applied.width * modelData.at
                    width: 1
                    height: applied.height
                    color: modelData.c
                }
            }

            Text {
                anchors { left: parent.left; top: parent.top; topMargin: 6 }
                visible: root.rows.length === 0
                text: "Nothing animates this element — press E for the library."
                color: Theme.inkFaint
                font.family: Theme.ui
                font.pixelSize: 12
            }

            ListView {
                anchors.fill: parent
                model: root.rows
                clip: true
                spacing: 7
                boundsBehavior: Flickable.StopAtBounds

                delegate: Item {
                    id: row
                    required property var modelData
                    width: ListView.view.width
                    height: 42

                    readonly property bool isMember: root.members.length > 0

                    // A statement that is commented out: it has a line and a
                    // name and no frames at all, because it never ran.
                    readonly property bool off: row.modelData.off === true

                    // A row can be edited when it knows the call that wrote it
                    // and that call is still where it said it was. An effect
                    // that came out of a loop, or from a helper the scene
                    // imported, keeps its bar and loses its handles rather than
                    // writing to a line it only half understands.
                    readonly property bool editable: !isMember
                                                     && modelData.line !== undefined && modelData.line > 0
                                                     && modelData.call !== undefined && modelData.call.length > 0
                                                     && Shell.callsOnLine(root.buffer, modelData.line)
                                                             .indexOf(modelData.call) >= 0

                    // Written on a `Group(...)` line: one call, every member.
                    // Said out loud, because the ✕ on this row takes the effect
                    // off the others too.
                    readonly property bool shared: editable
                                                   && Shell.callsOnLine(root.buffer, modelData.line)
                                                           .indexOf("Group") >= 0

                    // What the drag is worth so far, in seconds, before it is
                    // written. The bar follows these; the source does not, until
                    // the mouse comes up.
                    property real heldStart: 0
                    property real heldSpan: 0

                    // Tenths, unless ⌘ says otherwise — the same rule as
                    // dropping an effect, and the same reason: the ruler above
                    // is drawn in tenths.
                    function snap(seconds, free) {
                        return free ? Math.round(seconds * 100) / 100 : Math.round(seconds * 10) / 10;
                    }

                    // A value the card is allowed to do arithmetic on. An
                    // argument written as `RATIO * 0.5` is a number to Python
                    // and an expression to us: it keeps its bar, and the drag
                    // that would have rewritten it says why it did not.
                    function written(name, fallback) {
                        const text = Shell.readArgument(root.buffer, modelData.line, modelData.call, name);
                        if (text.length === 0)
                            return fallback;
                        const value = Number(text);
                        return isNaN(value) ? NaN : value;
                    }

                    function commit(name, value) {
                        if (isNaN(value)) {
                            root.effectWritten(modelData, "", "");
                            return;
                        }

                        // A gesture that lands back on the default writes
                        // nothing rather than writing `start=0`: an argument
                        // that says what the signature already says is noise the
                        // next reader has to check.
                        const rounded = Math.round(value * 100) / 100;
                        const already = Shell.readArgument(root.buffer, modelData.line, modelData.call, name);
                        if (rounded === 0 && already.length === 0)
                            return;
                        root.effectWritten(modelData, name, rounded.toString());
                    }

                    // The ✕ and the line number live at the far right of the
                    // ROW, not on the bar: a 0.4 s fade inside a three-second
                    // clip is a sliver, and a button that shrinks with what it
                    // acts on is a button you cannot press.
                    Row {
                        id: handle
                        anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                        spacing: 8
                        opacity: !row.off && row.editable && (hover.hovered || bar.pressed) ? 1 : 0
                        visible: opacity > 0
                        Behavior on opacity { NumberAnimation { duration: Theme.motion(110) } }

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: (row.shared ? "group · " : "") + "line " + row.modelData.line
                            color: Theme.inkFaint
                            font.family: Theme.mono
                            font.pixelSize: 10
                        }

                        // Off, not gone: the line stays in the scene, commented
                        // out, where you can read what it said and switch it
                        // back on. Deleting is the other button.
                        Rectangle {
                            width: 18; height: 18; radius: 9
                            anchors.verticalCenter: parent.verticalCenter
                            color: mute.containsMouse ? Qt.alpha(Theme.inkDim, 0.18) : "transparent"
                            border.width: 1
                            border.color: mute.containsMouse ? Theme.inkDim : Theme.inkFaint

                            Text {
                                anchors.centerIn: parent
                                text: "◦"
                                color: mute.containsMouse ? Theme.ink : Theme.inkDim
                                font.family: Theme.ui
                                font.pixelSize: 12
                            }

                            MouseArea {
                                id: mute
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.effectToggled(row.modelData.line, true)
                            }
                        }

                        Rectangle {
                            width: 18; height: 18; radius: 9
                            anchors.verticalCenter: parent.verticalCenter
                            color: cut.containsMouse ? "#33e05a4a" : "transparent"
                            border.width: 1
                            border.color: cut.containsMouse ? "#cce05a4a" : Theme.inkFaint

                            Text {
                                anchors.centerIn: parent
                                text: "✕"
                                color: cut.containsMouse ? "#ffe05a4a" : Theme.inkDim
                                font.family: Theme.ui
                                font.pixelSize: 10
                            }

                            MouseArea {
                                id: cut
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.effectRemoved(row.modelData)
                            }
                        }
                    }

                    HoverHandler { id: hover }

                    Rectangle {
                        id: span
                        visible: !row.off
                        x: row.width * Math.max(0, row.modelData.l - root.origin + row.heldStart) / root.span
                        width: Math.max(row.width * (row.modelData.d + row.heldSpan) / root.span, 3)
                        anchors { top: parent.top; bottom: parent.bottom; topMargin: 4; bottomMargin: 4 }
                        radius: 4
                        color: row.isMember
                               ? (Theme.kind[row.modelData.kind] !== undefined
                                  ? Theme.kind[row.modelData.kind] : root.hue)
                               : root.fxHue
                        clip: true

                        // Every complement on the wheel lands on the light, warm
                        // side, so dark ink beats white on an effect — and it
                        // separates what animates from what is animated, which
                        // carries light text on a saturated ground.
                        readonly property color ink: row.isMember ? "#eef3f9" : "#21160a"

                        // Wide enough to read it in: a 0.1 s effect on a
                        // four-second clip is three pixels of bar, and a name
                        // elided into nothing tells you only that something is
                        // there.
                        readonly property bool roomy: width > 96

                        Text {
                            anchors {
                                left: parent.left; leftMargin: 11
                                right: length.left; rightMargin: 12
                                verticalCenter: parent.verticalCenter
                            }
                            visible: span.roomy
                            text: row.modelData.n
                            color: span.ink
                            font.family: Theme.mono
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }

                        // Pushed to the far edge of the bar, so the number sits
                        // exactly where the effect ends — you read the duration
                        // and see it at the same time.
                        Text {
                            id: length
                            anchors { right: parent.right; rightMargin: 11; verticalCenter: parent.verticalCenter }
                            visible: span.roomy
                            text: (row.modelData.d + row.heldSpan).toFixed(1) + "s"
                            color: span.ink
                            opacity: 0.72
                            font.family: Theme.mono
                            font.pixelSize: 11
                        }

                        MouseArea {
                            anchors.fill: parent
                            enabled: row.isMember
                            onClicked: {
                                const at = row.mapToItem(null, span.x, 0);
                                root.memberOpened(row.modelData,
                                                  Qt.rect(at.x, at.y, span.width, row.height));
                            }
                        }
                    }

                    // Moving the bar writes `start=`, dragging its right edge
                    // writes `duration=`. Both as a DELTA on what the line
                    // already says: `start` is counted from the element's own
                    // cursor, and the card has no business working out where
                    // that cursor is — only how much further along the person
                    // just asked for.
                    MouseArea {
                        id: dragBar
                        enabled: row.editable && !row.off
                        anchors.fill: span
                        hoverEnabled: true
                        cursorShape: onEdge || edging ? Qt.SizeHorCursor
                                   : (pressed ? Qt.ClosedHandCursor : Qt.PointingHandCursor)

                        property real anchorX: 0
                        property bool edging: false
                        property bool moved: false
                        readonly property bool onEdge: containsMouse && mouseX > width - 9

                        function seconds(dx) {
                            return dx * root.span / Math.max(row.width, 1);
                        }

                        // Measured against the ROW, never against itself. The
                        // bar is what the drag moves, so a delta taken in the
                        // bar's own coordinates shrinks by exactly as much as
                        // the bar travels — the two cancel, and a drag of half a
                        // second writes `start=0`.
                        onPressed: (mouse) => {
                            anchorX = mapToItem(row, mouse.x, 0).x;
                            // Read from the press itself. `onEdge` also asks
                            // whether the pointer is inside, and a press that
                            // arrives without a hover before it — every
                            // scripted one, and a tap — says it is not.
                            edging = mouse.x > width - 9;
                            moved = false;
                        }

                        onPositionChanged: (mouse) => {
                            if (!pressed)
                                return;
                            const now = mapToItem(row, mouse.x, 0).x;
                            const delta = row.snap(seconds(now - anchorX), (mouse.modifiers & Qt.ControlModifier) !== 0);
                            if (Math.abs(delta) > 0.001)
                                moved = true;
                            if (edging)
                                // A bar cannot be shortened past nothing: a
                                // `duration` of zero is a change with no time to
                                // happen in, which the scene draws as a jump.
                                row.heldSpan = Math.max(0.1 - row.modelData.d, delta);
                            else
                                // `start` is counted from the element's own
                                // cursor and cannot go behind it: an effect
                                // dragged to the left of where its element is
                                // ready is asking to happen before the line
                                // that schedules it.
                                row.heldStart = Math.max(-row.written("start", 0), delta);
                        }

                        onReleased: {
                            if (!moved) {
                                row.heldStart = 0;
                                row.heldSpan = 0;
                                // A press that went nowhere is a click, and a
                                // click on an effect asks to see the line that
                                // wrote it.
                                root.effectJumped(row.modelData);
                                return;
                            }
                            if (edging)
                                row.commit("duration", row.written("duration", row.modelData.d) + row.heldSpan);
                            else
                                row.commit("start", row.written("start", 0) + row.heldStart);
                            // Held only until the scene comes back saying where
                            // the bar really is — the source is the truth, and
                            // keeping the offset would draw the move twice.
                            row.heldStart = 0;
                            row.heldSpan = 0;
                        }
                    }

                    // A statement that is off: the line itself, greyed, with the
                    // switch to bring it back. No bar — it covers no time,
                    // because it did not happen.
                    Rectangle {
                        visible: row.off
                        anchors { left: parent.left; right: parent.right; top: parent.top; bottom: parent.bottom }
                        anchors.margins: 4
                        radius: 4
                        color: back.containsMouse ? Qt.alpha(Theme.live, 0.06) : "transparent"
                        border.width: 1
                        border.color: back.containsMouse ? Qt.alpha(Theme.live, 0.5) : Theme.edge

                        Text {
                            anchors { left: parent.left; leftMargin: 11; right: switchOn.left; rightMargin: 10; verticalCenter: parent.verticalCenter }
                            text: "# " + (row.modelData.said !== undefined ? row.modelData.said : row.modelData.n)
                            color: Theme.inkFaint
                            font.family: Theme.mono
                            font.pixelSize: 12
                            elide: Text.ElideRight
                        }

                        Text {
                            id: switchOn
                            anchors { right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
                            text: back.containsMouse ? "switch it back on" : "off"
                            color: back.containsMouse ? Theme.live : Theme.inkFaint
                            font.family: Theme.ui
                            font.pixelSize: 10
                        }

                        MouseArea {
                            id: back
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.effectToggled(row.modelData.line, false)
                        }
                    }

                    // What a bar too narrow to hold its name says, beside it.
                    Text {
                        anchors { left: span.right; leftMargin: 9; verticalCenter: span.verticalCenter }
                        visible: !span.roomy && !row.off
                        text: row.modelData.n + "  " + (row.modelData.d + row.heldSpan).toFixed(1) + "s"
                        color: row.isMember ? Theme.ink : root.fxHue
                        font.family: Theme.mono
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                    }

                    // The edge you can take hold of, shown only while the mouse
                    // is on it.
                    Rectangle {
                        x: span.x + span.width - 3
                        width: 2
                        anchors { top: span.top; bottom: span.bottom; topMargin: 5; bottomMargin: 5 }
                        radius: 1
                        color: span.ink
                        opacity: bar.onEdge || bar.edging ? 0.8 : 0
                        Behavior on opacity { NumberAnimation { duration: Theme.motion(90) } }
                    }
                }
            }
        }

        // ── The line that made it, as values you can change ───────────────
        // The chips ARE the call: what the source says, in the order the
        // signature declares. A value that is not written shows its default,
        // dimmed — writing it adds it to the line; clearing it takes it back
        // out. Trimming a video is `endFrame` here, and nothing in this card
        // knows that is what trimming means.
        Flow {
            id: argRow
            anchors {
                left: bar.left; right: bar.right
                bottom: hint.top; bottomMargin: 10
            }
            spacing: 6
            visible: root.arguments.length > 0

            Repeater {
                model: root.arguments

                Rectangle {
                    id: arg
                    required property var modelData

                    readonly property string current: root.written(arg.modelData.name)
                    readonly property bool set: current.length > 0

                    height: 22
                    width: argName.implicitWidth + argValue.width + 22
                    radius: 4
                    color: argEntry.activeFocus ? Qt.alpha(root.fxHue, 0.12) : Theme.sunk
                    border.width: 1
                    border.color: argEntry.activeFocus
                                  ? root.fxHue
                                  : (arg.set ? Theme.edge : Theme.edgeSoft)

                    Text {
                        id: argName
                        anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                        text: arg.modelData.name
                        color: arg.set ? Theme.inkDim : Theme.inkFaint
                        font.family: Theme.mono
                        font.pixelSize: 11
                    }

                    Item {
                        id: argValue
                        anchors { left: argName.right; leftMargin: 6; verticalCenter: parent.verticalCenter }
                        width: Math.max(argEntry.implicitWidth + 4, 26)
                        height: 16

                        TextInput {
                            id: argEntry
                            anchors.fill: parent
                            verticalAlignment: TextInput.AlignVCenter
                            // What the source says, or the signature's default
                            // shown for what it is: a value nobody chose.
                            text: arg.set ? arg.current : arg.modelData.value
                            color: arg.set ? Theme.ink : Theme.inkFaint
                            font.family: Theme.mono
                            font.pixelSize: 11
                            selectByMouse: true
                            selectionColor: Qt.alpha(root.fxHue, 0.4)
                            enabled: root.writable

                            // On Enter, not on every keystroke: a scene that
                            // re-runs on each character would run on `1.`, on
                            // `1.5` and on everything in between.
                            onAccepted: arg.commit()
                            onActiveFocusChanged: if (!activeFocus) arg.commit()
                            Keys.onEscapePressed: {
                                argEntry.text = arg.set ? arg.current : arg.modelData.value;
                                root.forceActiveFocus();
                            }
                        }
                    }

                    function commit() {
                        const value = argEntry.text.trim();
                        if (!root.writable || value === arg.current)
                            return;
                        if (value.length === 0 || value === arg.modelData.value)
                            return;
                        root.argumentWritten(root.element, root.cls, arg.modelData.name, value);
                    }

                    MouseArea {
                        anchors.fill: parent
                        enabled: !argEntry.activeFocus
                        cursorShape: root.writable ? Qt.IBeamCursor : Qt.ArrowCursor
                        onClicked: {
                            if (!root.writable)
                                return;
                            argEntry.forceActiveFocus();
                            argEntry.selectAll();
                        }
                    }
                }
            }
        }

        // ── How to get out, and how to add one ────────────────────────────
        Item {
            id: hint
            anchors {
                left: bar.left; right: bar.right
                bottom: parent.bottom; bottomMargin: card.pad
            }
            height: 22

            Rectangle {
                anchors { left: parent.left; right: parent.right; top: parent.top }
                height: 1
                color: Theme.edge
            }

            Text {
                anchors { left: parent.left; bottom: parent.bottom }
                textFormat: Text.StyledText
                text: "<b>E</b> for the effects library · click outside or <b>Esc</b> to go back"
                color: Theme.inkFaint
                font.family: Theme.ui
                font.pixelSize: 11
            }
        }
    }

    // ── The bar, on its way ───────────────────────────────────────────────
    // The clip you clicked, between its lane and the middle of the window.
    //
    // It is not a copy dressed as one: the lane it left is drawn hollow for
    // exactly as long as this exists, so at no point are there two of the same
    // element on screen. What changes along the way is what the two ends look
    // like — a clip is a translucent bar with a name band, a block is a solid one
    // with the name across it — so the look is interpolated on the same clock as
    // the geometry rather than swapped at either end.
    Rectangle {
        id: flight

        readonly property real t: root.travel
        readonly property real toX: card.x + card.pad
        readonly property real toY: card.y + card.pad + 12 + 10
        readonly property real toWidth: card.width - card.pad * 2
        readonly property real toHeight: 76

        visible: root.element !== null && t < 1
        z: 4

        x: root.from.x + (toX - root.from.x) * t
        y: root.from.y + (toY - root.from.y) * t
        width: Math.max(1, root.from.width + (toWidth - root.from.width) * t)
        height: Math.max(1, root.from.height + (toHeight - root.from.height) * t)

        color: Qt.alpha(root.hue, 0.30 + 0.70 * t)
        radius: 4 + 2 * t
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.15 + 0.03 * t)
        clip: true

        Row {
            anchors { fill: parent; margins: 4; topMargin: 4 + 15 * (1 - flight.t) }
            spacing: 1
            visible: root.kind === "video" || root.kind === "sound"
            opacity: 0.55 - 0.21 * flight.t

            Repeater {
                model: Math.max(Math.round(root.span * 10), 1)

                Rectangle {
                    required property int index
                    readonly property real v: 22 + 78 * Math.abs(
                        Math.sin(index * 0.7) * Math.cos(index * 0.21) * Math.sin(index * 0.05 + 1))
                    width: Math.max((flight.width - 8) / Math.max(Math.round(root.span * 10), 1) - 1, 1)
                    height: parent.height * v / 100
                    anchors.verticalCenter: parent.verticalCenter
                    radius: 1
                    color: "#dff3ee"
                }
            }
        }

        // The clip's name band, on its way out.
        Rectangle {
            anchors { left: parent.left; right: parent.right; top: parent.top }
            anchors.margins: 1
            height: 16 * (1 - flight.t)
            topLeftRadius: 3
            topRightRadius: 3
            color: Qt.alpha(root.hue, 0.92)
            clip: true
            opacity: 1 - flight.t

            Text {
                anchors { left: parent.left; leftMargin: 6; verticalCenter: parent.verticalCenter }
                text: root.element !== null ? root.element.n : ""
                color: Qt.rgba(0.04, 0.06, 0.09, 0.92)
                font.family: Theme.ui
                font.pixelSize: 11
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
        }

        // The block's name, on its way in.
        Text {
            anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
            text: root.element !== null ? root.element.n : ""
            color: "#eef3f9"
            font.family: Theme.ui
            font.pixelSize: 15
            font.weight: Font.DemiBold
            style: Text.Outline
            styleColor: Qt.rgba(0.043, 0.055, 0.075, 0.85)
            opacity: flight.t
        }
    }

    // ── The library, summoned with E ──────────────────────────────────────
    // Over the card rather than beside it: it is aimed at the block, used, and
    // dismissed, and a permanent column would narrow the block for the whole
    // time it is not there.
    Rectangle {
        id: lib
        z: 5
        visible: opacity > 0
        // Centred, it sits over the very block you are aiming at — so the moment
        // the drag starts it gets out of the way, and takes none of the drop.
        opacity: root.library ? (root.dragging ? 0.12 : 1) : 0
        scale: root.library ? 1 : 0.96
        x: (root.width - width) / 2
        y: (root.height - height) / 2
        width: Math.min(420, root.width - 40)
        height: root.picked !== null
                ? Math.min(root.height * 0.66, fields.contentHeight + carry.height + 96)
                : Math.min(root.height * 0.66, list.contentHeight + 84)
        color: Theme.panel
        radius: Theme.radius
        border.width: 1
        border.color: Theme.edge

        Behavior on opacity { NumberAnimation { duration: Theme.motion(160) } }
        Behavior on scale { NumberAnimation { duration: Theme.motion(180); easing.type: Easing.OutCubic } }

        MouseArea { anchors.fill: parent }

        Item {
            id: libHead
            anchors { left: parent.left; right: parent.right; top: parent.top }
            anchors.margins: 14
            height: 22

            Text {
                id: libTitle
                anchors.left: parent.left
                text: root.picked === null ? "EFFECTS" : root.picked.name
                color: root.picked === null ? Theme.inkFaint : Theme.ink
                font.family: root.picked === null ? Theme.ui : Theme.mono
                font.pixelSize: root.picked === null ? 10 : 12
                font.weight: Font.DemiBold
                font.letterSpacing: root.picked === null ? 0.9 : 0
            }

            Text {
                anchors.right: parent.right
                text: root.picked === null ? root.effectNames.length : "back"
                color: backLink.containsMouse ? Theme.live : Theme.inkDim
                font.family: Theme.mono
                font.pixelSize: 11

                MouseArea {
                    id: backLink
                    anchors.fill: parent
                    anchors.margins: -6
                    enabled: root.picked !== null
                    hoverEnabled: true
                    onClicked: root.unpick()
                }
            }

            Rectangle {
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                height: 1
                color: Theme.edge
            }
        }

        ListView {
            id: list
            visible: root.picked === null
            anchors {
                left: parent.left; right: parent.right
                top: libHead.bottom; topMargin: 4
                bottom: libHint.top; bottomMargin: 8
            }
            anchors.leftMargin: 14
            anchors.rightMargin: 14
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            // Grouped by where the effect lives, because that is what the import
            // will say: `videocode.template.effect.entrance.fade` is an
            // entrance, and the chip that writes the line should say so.
            model: {
                const groups = [];
                const seen = ({});
                for (const fx of root.effectNames) {
                    const parts = String(fx.module).split(".");
                    const family = parts.length > 3 ? parts[3] : "effect";
                    if (seen[family] === undefined) {
                        seen[family] = { name: family, items: [] };
                        groups.push(seen[family]);
                    }
                    seen[family].items.push(fx);
                }
                return groups;
            }

            delegate: Column {
                id: family
                required property var modelData
                width: ListView.view.width
                spacing: 6
                bottomPadding: 5

                Text {
                    text: family.modelData.name.toUpperCase()
                    color: Theme.inkFaint
                    font.family: Theme.ui
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                    font.letterSpacing: 0.9
                    topPadding: 6
                }

                Flow {
                    width: parent.width
                    spacing: 6

                    Repeater {
                        model: family.modelData.items

                        Rectangle {
                            id: chip
                            required property var modelData
                            width: label.implicitWidth + 18
                            height: 22
                            radius: 4
                            color: pick.containsMouse ? Qt.alpha(root.fxHue, 0.14) : Theme.sunk
                            border.width: 1
                            border.color: pick.containsMouse ? root.fxHue : Theme.edge

                            Text {
                                id: label
                                anchors.centerIn: parent
                                text: chip.modelData.name
                                color: pick.containsMouse ? Theme.ink : Theme.inkDim
                                font.family: Theme.mono
                                font.pixelSize: 11
                            }

                            MouseArea {
                                id: pick
                                anchors.fill: parent
                                hoverEnabled: true
                                // Chosen, not applied. What it is set to and
                                // where it lands are still open questions, and
                                // an effect written into the scene the instant
                                // you name it answers both of them for you.
                                onClicked: root.pick(chip.modelData)
                            }
                        }
                    }
                }
            }
        }

        // What the effect takes, in the field idiom the rest of the chrome uses.
        // Whatever is left at its default is not written into the call: a line
        // that repeats the signature back to it is noise you have to read past
        // every time you open the scene.
        ListView {
            id: fields
            visible: root.picked !== null
            anchors {
                left: parent.left; right: parent.right
                top: libHead.bottom; topMargin: 6
                bottom: carry.top; bottomMargin: 10
            }
            anchors.leftMargin: 14
            anchors.rightMargin: 14
            clip: true
            spacing: 6
            boundsBehavior: Flickable.StopAtBounds
            model: root.picked !== null ? root.picked.params : []

            delegate: Item {
                id: field
                required property var modelData
                width: ListView.view.width
                height: 26

                readonly property bool needed: field.modelData.value.length === 0

                Text {
                    id: fieldName
                    anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                    width: 96
                    text: field.modelData.name
                    color: field.needed ? Theme.ink : Theme.inkDim
                    font.family: Theme.mono
                    font.pixelSize: 11
                    elide: Text.ElideRight
                }

                Rectangle {
                    anchors {
                        left: fieldName.right; leftMargin: 8
                        right: parent.right
                        verticalCenter: parent.verticalCenter
                    }
                    height: 24
                    radius: Theme.radiusSmall
                    color: Theme.sunk
                    border.width: 1
                    border.color: entry.activeFocus
                                  ? root.fxHue
                                  : (field.needed && entry.text.trim().length === 0 ? Theme.bad : Theme.edge)

                    TextInput {
                        id: entry
                        anchors { fill: parent; leftMargin: 8; rightMargin: 8 }
                        verticalAlignment: TextInput.AlignVCenter
                        // Filled once, never bound: a field bound to the same
                        // table it writes back into is a binding loop, and Qt
                        // breaks it by dropping the binding — which is to say by
                        // dropping whichever of the two you happened to do last.
                        Component.onCompleted: entry.text = root.values[field.modelData.name] !== undefined
                                               ? root.values[field.modelData.name] : field.modelData.value
                        color: Theme.ink
                        font.family: Theme.mono
                        font.pixelSize: 11
                        selectByMouse: true
                        selectionColor: Qt.alpha(root.fxHue, 0.4)

                        // Out of the field first. A TextInput swallows the key
                        // it is given, so without this the card's own Escape
                        // never runs and the whole thing feels stuck.
                        Keys.onEscapePressed: root.forceActiveFocus()

                        // Written straight through: the field IS the argument,
                        // and a value the editor second-guessed would be a value
                        // the scene does not contain.
                        //
                        // A fresh table rather than a poke into the old one: the
                        // duration below is computed FROM it, and mutating an
                        // object in place tells QML nothing.
                        onTextEdited: {
                            const next = ({});
                            for (const key in root.values)
                                next[key] = root.values[key];
                            next[field.modelData.name] = text;
                            root.values = next;
                        }
                    }

                    Text {
                        anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                        visible: entry.text.trim().length === 0 && field.needed
                        text: field.modelData.kind
                        color: Theme.inkFaint
                        font.family: Theme.mono
                        font.pixelSize: 10
                    }
                }
            }
        }

        // The effect itself, at the length its fields give it — picked up from
        // here and carried onto the element.
        Item {
            id: carry
            visible: root.picked !== null
            anchors {
                left: parent.left; right: parent.right
                bottom: libHint.top; bottomMargin: 8
            }
            anchors.leftMargin: 14
            anchors.rightMargin: 14
            height: 34

            Rectangle {
                anchors.fill: parent
                radius: 4
                color: root.missing.length > 0 ? Theme.sunk : root.fxHue
                border.width: 1
                border.color: root.missing.length > 0 ? Theme.edge : root.fxHue

                Text {
                    anchors.centerIn: parent
                    text: root.picked === null
                          ? ""
                          : (root.missing.length > 0
                             ? root.missing.join(", ") + " — needed"
                             : root.picked.name + "   " + root.pickedDuration.toFixed(2) + "s")
                    color: root.missing.length > 0 ? Theme.inkFaint : "#21160a"
                    font.family: Theme.mono
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }

                MouseArea {
                    anchors.fill: parent
                    enabled: root.missing.length === 0
                    cursorShape: enabled ? Qt.OpenHandCursor : Qt.ArrowCursor
                    // ⌘ is read on every move, not only on the press: you decide
                    // to drop exactly here in the middle of aiming, which is the
                    // moment you can see that the snap is one tenth off.
                    onPressed: (mouse) => {
                        root.exact = (mouse.modifiers & Qt.ControlModifier) !== 0;
                        root.dragging = true;
                        const at = mapToItem(null, mouse.x, mouse.y);
                        root.dropAt = root.timeAt(at.x);
                    }

                    onPositionChanged: (mouse) => {
                        if (!pressed)
                            return;
                        root.exact = (mouse.modifiers & Qt.ControlModifier) !== 0;
                        const at = mapToItem(null, mouse.x, mouse.y);
                        root.dropAt = root.timeAt(at.x);
                    }

                    onReleased: (mouse) => {
                        if (!root.dragging)
                            return;
                        root.dragging = false;

                        // Dropped on the element or nowhere: the block is the
                        // only surface that means anything here, and a release
                        // over the rest of the card cancels rather than guessing.
                        const at = mapToItem(null, mouse.x, mouse.y);
                        const inside = bar.mapFromItem(null, at.x, at.y);
                        if (inside.x < 0 || inside.x > bar.width || inside.y < 0 || inside.y > bar.height)
                            return;

                        // Where it lands, counted from the START OF THE SCENE.
                        // The card measures from the element's own left edge —
                        // that is what its axis shows — but the statement has to
                        // be written where the element's cursor makes it land
                        // there, and only the shell knows where that is.
                        root.effectRequested(root.element, root.picked, {
                            at: root.origin + root.dropAt,
                            values: root.values
                        });
                        root.library = false;
                        root.unpick();
                    }
                }
            }
        }

        Text {
            id: libHint
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            anchors.margins: 12
            textFormat: Text.StyledText
            text: root.picked === null
                  ? "Click one to set it up."
                  : "Drag it onto the element · snaps to 0.1 s, hold <b>⌘</b> to drop exactly"
            color: Theme.inkFaint
            font.family: Theme.ui
            font.pixelSize: 11
        }
    }

    // Escape, one step at a time: the field you are typing in, then the effect
    // you were setting up, then the library, then the card. Anything else and a
    // stray key in a parameter box would throw away the whole thing you opened.
    Keys.onEscapePressed: dismiss()

    function dismiss() {
        if (picked !== null)
            unpick();
        else if (library)
            library = false;
        else
            close();
    }

    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_E && root.members.length === 0) {
            // A group has no `apply` of its own: offering the library there
            // would write a line naming something the scene does not have.
            root.library = !root.library;
            event.accepted = true;
        }
    }

    onVisibleChanged: {
        if (visible)
            forceActiveFocus();
        else
            library = false;
    }
}
