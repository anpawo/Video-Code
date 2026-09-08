// The board, and what it is bound to.
//
// A list of shortcuts tells you what exists; a KEYBOARD tells you where to put
// your hand, which is the actual question. Press a key and the whole
// combination lights up — modifiers included, so there is no layer to switch to
// — and a card under the board says what it does and stays there until the next
// key. Pointing at an action, or at a cap that carries one thing, says the same.
//
// Rebinding is by pressing the keys, not by picking from a list of names: the
// gesture that sets the shortcut is the gesture that uses it. Everything here
// reads and writes Keymap, which is the same table the code pane consults — the
// board can never be out of date with what the keys actually do.
pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: root
    anchors.fill: parent
    visible: false

    // The action whose combination is being captured, or "".
    property string capturing: ""

    // Lit keys, by token: filled while an action is hovered.
    property var hot: []

    // A rebinding that would have stolen a key, and from whom.
    property string clash: ""

    // The combination the card under the board is answering for. Set by a key
    // you press, or by an action you point at, and it STAYS there until
    // something else replaces it: press, read, press again — nothing to chase.
    property string struck: ""

    // One row per physical key. The third number widens a key in flex units;
    // "mod" marks the ones that are held rather than struck.
    readonly property var board: [
        [["esc", "Esc", 1.5], ["F1", "F1"], ["F2", "F2"], ["F3", "F3"], ["F4", "F4"], ["F5", "F5"],
         ["F6", "F6"], ["F7", "F7"], ["F8", "F8"], ["F9", "F9"], ["F10", "F10"], ["F11", "F11"], ["F12", "F12"]],
        [["`", "`"], ["1", "1"], ["2", "2"], ["3", "3"], ["4", "4"], ["5", "5"], ["6", "6"], ["7", "7"],
         ["8", "8"], ["9", "9"], ["0", "0"], ["-", "-"], ["=", "="], ["⌫", "Backspace", 2]],
        [["⇥", "Tab", 1.5], ["Q", "Q"], ["W", "W"], ["E", "E"], ["R", "R"], ["T", "T"], ["Y", "Y"],
         ["U", "U"], ["I", "I"], ["O", "O"], ["P", "P"], ["[", "["], ["]", "]"], ["\\", "\\", 1.5]],
        [["caps", "CapsLock", 2], ["A", "A"], ["S", "S"], ["D", "D"], ["F", "F"], ["G", "G"], ["H", "H"],
         ["J", "J"], ["K", "K"], ["L", "L"], [";", ";"], ["'", "'"], ["⏎", "Enter", 2]],
        [["⇧", "Shift", 2.5, "mod"], ["Z", "Z"], ["X", "X"], ["C", "C"], ["V", "V"], ["B", "B"],
         ["N", "N"], ["M", "M"], [",", ","], [".", "."], ["/", "/"], ["⇧", "Shift", 2.5, "mod"]],
        [["⌃", "Ctrl", 1.5, "mod"], ["⌥", "Alt", 1.5, "mod"], ["⌘", "Cmd", 1.5, "mod"],
         ["space", "Space", 6], ["⌘", "Cmd", 1.5, "mod"], ["⌥", "Alt", 1.5, "mod"],
         ["←", "←"], ["↑", "↑"], ["↓", "↓"], ["→", "→"]]
    ]

    // What is bound to a key, for the label under the board.
    function boundTo(token) {
        let out = [];
        for (const action of Keymap.actions)
            if (Keymap.baseOf(Keymap.combo(action.id)) === token)
                out.push(action.label + " · " + Keymap.combo(action.id));
        for (const one of Keymap.reserved)
            if (Keymap.baseOf(one.key) === token)
                out.push(one.label + " · " + one.key);
        return out.join("   ");
    }

    // The one combination that ends on this cap, for pointing at a cap. Empty
    // when the cap carries nothing, or more than one thing — a cap under two
    // combinations has no single answer, and the card answers with one.
    function boundSpec(token) {
        let out = [];
        for (const action of Keymap.actions)
            if (Keymap.baseOf(Keymap.combo(action.id)) === token)
                out.push(Keymap.combo(action.id));
        for (const one of Keymap.reserved)
            if (Keymap.baseOf(one.key) === token)
                out.push(one.key);
        return out.length === 1 ? out[0] : "";
    }

    readonly property var held: ["Cmd", "Ctrl", "Shift", "Alt"]

    // The action a combination fires, or null. Reserved rows answer too: they
    // are keys the menu bar owns, and "taken by the menu bar" is an answer.
    function firing(spec) {
        for (const action of Keymap.actions)
            if (Keymap.combo(action.id) === spec)
                return action;
        for (const one of Keymap.reserved)
            if (one.key === spec)
                return one;
        return null;
    }

    function heading() {
        const one = root.firing(root.struck);
        return one !== null ? one.label : "Nothing on it";
    }

    // At most three lines. The qualifier is added here rather than written into
    // the table, so an action that gains or loses it says so by itself.
    function bullets() {
        const spec = root.struck;
        if (root.held.indexOf(spec) >= 0)
            return ["Held on its own. Press a combination to see whether it is taken."];

        const one = root.firing(spec);
        if (one === null) {
            // "⌘I does nothing" is half an answer while I on its own marks in.
            const rest = root.boundTo(Keymap.baseOf(spec));
            return rest.length > 0
                   ? ["Nothing is bound to it.", "On this key: " + rest]
                   : ["Nothing is bound to it."];
        }

        let out = (one.says !== undefined ? one.says.slice(0, 3) : []);
        if (one.key !== undefined)
            out.push("The menu bar answers it, so it cannot be rebound here.");
        else if (one.only !== undefined && !Keymap.survivesTyping(one.id))
            out.push("Works " + one.only + " — while the caret is in it, this key writes.");
        return out.slice(0, 3);
    }

    // A modifier struck alone is not a combination: nothing fires, but the cap
    // has to light or the board looks deaf to half of what you press.
    function modifierToken(key) {
        if (key === Qt.Key_Control) return "Cmd";
        if (key === Qt.Key_Meta)    return "Ctrl";
        if (key === Qt.Key_Shift)   return "Shift";
        if (key === Qt.Key_Alt)     return "Alt";
        return "";
    }

    // One door for both ways in: a key you pressed and an action you pointed at
    // put the same thing on screen, so the caps and the card can never disagree.
    function showSpec(spec) {
        if (spec.length === 0)
            return;
        root.struck = spec;
        root.hot = root.held.indexOf(spec) >= 0
                   ? [spec]
                   : Keymap.modsOf(spec).concat([Keymap.baseOf(spec)]);
    }

    function stopCapturing() {
        root.capturing = "";
        root.clash = "";
    }

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.6)

        MouseArea {
            anchors.fill: parent
            onClicked: root.visible = false
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: Math.min(940, root.width - 60)
        // Tall enough for whichever column needs more: the board on the left or
        // the list on the right. Sized from the content rather than fixed,
        // because adding an action must not quietly clip the last row off.
        height: Math.min(
            Math.max(keyboard.height + 96 + Math.max(answer.height, invite.height + 8),
                     (Keymap.actions.length + Keymap.reserved.length) * 28 + 92),
            root.height - 60)
        color: Theme.panel
        radius: Theme.radius
        border.width: 1
        border.color: Theme.edge

        MouseArea { anchors.fill: parent }

        Text {
            id: title
            anchors { left: parent.left; leftMargin: 20; top: parent.top; topMargin: 16 }
            text: "Keyboard"
            color: Theme.ink
            font.family: Theme.ui
            font.pixelSize: 13
        }

        Text {
            anchors { right: closer.left; rightMargin: 8; verticalCenter: title.verticalCenter }
            text: root.capturing.length > 0 ? "esc to cancel" : "esc"
            color: root.capturing.length > 0 ? Theme.live : Theme.inkFaint
            font.family: Theme.mono
            font.pixelSize: 10
        }

        CloseButton {
            id: closer
            anchors { right: parent.right; rightMargin: 14; verticalCenter: title.verticalCenter }
            onTriggered: root.visible = false
        }

        // ── The board ─────────────────────────────────────────────────────
        // Uniform on purpose. Marking every taken key turned it into a heat map
        // of things nobody asked about; the only question it answers is "where
        // do I press for THIS", and it answers by lighting the whole combination.
        Item {
            id: keyboard
            anchors {
                left: parent.left; leftMargin: 20
                right: actions.left; rightMargin: 20
                top: title.bottom; topMargin: 16
            }
            height: rows.implicitHeight

            Column {
                id: rows
                width: parent.width
                spacing: 4

                Repeater {
                    model: root.board

                    Row {
                        id: line
                        required property var modelData
                        spacing: 4

                        // Every row spans the board, and rows do not hold the
                        // same number of units — the bottom one is 17.5 wide
                        // against the top one's 13.5. So the unit is per ROW,
                        // which is exactly what a flex row does and what keeps
                        // the right-hand edge straight.
                        readonly property real units: {
                            let total = 0;
                            for (const key of line.modelData)
                                total += key.length > 2 ? key[2] : 1;
                            return total;
                        }
                        readonly property real unit:
                            (keyboard.width - (line.modelData.length - 1) * spacing) / line.units

                        Repeater {
                            model: line.modelData

                            Rectangle {
                                id: cap
                                required property var modelData
                                readonly property real units: cap.modelData.length > 2 ? cap.modelData[2] : 1
                                readonly property string token: cap.modelData[1]
                                readonly property bool lit: root.hot.indexOf(cap.token) >= 0
                                readonly property bool held: cap.modelData.length > 3

                                width: line.unit * cap.units
                                height: 30
                                radius: Theme.radiusSmall
                                color: cap.lit ? Qt.alpha(Theme.live, 0.22)
                                               : (keyHit.containsMouse ? Theme.rail : Theme.sunk)
                                border.width: 1
                                border.color: cap.lit ? Theme.live : Theme.edge

                                Text {
                                    anchors.centerIn: parent
                                    text: cap.modelData[0]
                                    color: cap.lit ? Theme.live : (cap.held ? Theme.inkFaint : Theme.inkDim)
                                    font.family: Theme.mono
                                    font.pixelSize: cap.modelData[0].length > 2 ? 9 : 11
                                }

                                MouseArea {
                                    id: keyHit
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onEntered: root.showSpec(root.boundSpec(cap.token))
                                }
                            }
                        }
                    }
                }
            }
        }

        // Which modifier is PHYSICALLY down, left or right.
        //
        // Qt cannot tell the two ⌥ keys apart — `Qt.AltModifier` means "an Alt
        // key" — but macOS reports the side beside the ordinary flags, and the
        // shell reads them off every key event. Shown here because a claim
        // about a keyboard is worth nothing until you have pressed the key and
        // seen it answer.
        Row {
            id: sides
            anchors { left: keyboard.left; top: keyboard.bottom; topMargin: 12 }
            spacing: 6
            visible: Shell.modifierSides !== 0

            Repeater {
                model: [
                    { bit: 1 << 4, label: "⇧ gauche" }, { bit: 1 << 5, label: "⇧ droite" },
                    { bit: 1 << 6, label: "⌃ gauche" }, { bit: 1 << 7, label: "⌃ droite" },
                    { bit: 1 << 2, label: "⌥ gauche" }, { bit: 1 << 3, label: "⌥ droite" },
                    { bit: 1 << 0, label: "⌘ gauche" }, { bit: 1 << 1, label: "⌘ droite" }
                ]

                Rectangle {
                    required property var modelData
                    visible: (Shell.modifierSides & modelData.bit) !== 0
                    width: side.implicitWidth + 14
                    height: 20
                    radius: Theme.radiusSmall
                    color: Qt.alpha(Theme.live, 0.18)
                    border.width: 1
                    border.color: Theme.live

                    Text {
                        id: side
                        anchors.centerIn: parent
                        text: parent.modelData.label
                        color: Theme.live
                        font.family: Theme.mono
                        font.pixelSize: 10
                    }
                }
            }
        }

        // ── What the last key does ────────────────────────────────────────
        // An invitation until you press something, then a card: the action's
        // name, the keys you held, and what it does in at most three lines. It
        // stays until the next key replaces it — press, read, press again,
        // with nothing to chase and nothing to hover.
        Text {
            id: invite
            anchors { left: keyboard.left; top: sides.bottom; topMargin: 16 }
            visible: root.struck.length === 0
            text: "Press any key"
            color: Theme.inkDim
            font.family: Theme.ui
            font.pixelSize: 17
        }

        Rectangle {
            id: answer
            anchors {
                left: keyboard.left; right: keyboard.right
                top: sides.bottom; topMargin: 12
            }
            visible: root.struck.length > 0
            height: name.height + says.height + 26
            radius: Theme.radius
            color: Theme.sunk
            border.width: 1
            border.color: Theme.edge

            Text {
                id: name
                anchors { left: parent.left; leftMargin: 14; right: chip.left; rightMargin: 10; top: parent.top; topMargin: 12 }
                text: root.struck.length > 0 ? root.heading() : ""
                color: Theme.ink
                font.family: Theme.ui
                font.pixelSize: 14
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }

            // The keys themselves, written the way the caps are.
            Rectangle {
                id: chip
                anchors { right: parent.right; rightMargin: 14; verticalCenter: name.verticalCenter }
                width: Math.max(pressed.implicitWidth + 16, 40)
                height: 22
                radius: Theme.radiusSmall
                color: Qt.alpha(Theme.live, 0.18)
                border.width: 1
                border.color: Theme.live

                Text {
                    id: pressed
                    anchors.centerIn: parent
                    text: root.struck.replace(/Cmd/g, "⌘").replace(/Ctrl/g, "⌃")
                                     .replace(/Shift/g, "⇧").replace(/Alt/g, "⌥")
                                     .replace(/\+/g, "")
                    color: Theme.live
                    font.family: Theme.mono
                    font.pixelSize: 11
                }
            }

            Column {
                id: says
                anchors { left: parent.left; leftMargin: 14; right: parent.right; rightMargin: 14; top: name.bottom; topMargin: 6 }
                spacing: 2

                Repeater {
                    model: root.struck.length > 0 ? root.bullets() : []

                    Text {
                        required property string modelData
                        width: says.width
                        text: "·  " + modelData
                        color: Theme.inkDim
                        font.family: Theme.ui
                        font.pixelSize: 12
                        wrapMode: Text.Wrap
                    }
                }
            }
        }

        // ── The actions ───────────────────────────────────────────────────
        Item {
            id: actions
            anchors {
                right: parent.right; rightMargin: 20
                top: title.bottom; topMargin: 16
                bottom: parent.bottom; bottomMargin: 18
            }
            width: 250

            Text {
                id: head
                text: "ACTIONS"
                color: Theme.inkFaint
                font.family: Theme.ui
                font.pixelSize: 10
                font.letterSpacing: 0.8
            }

            Rectangle {
                id: warning
                anchors { left: parent.left; right: parent.right; top: head.bottom; topMargin: 8 }
                height: visible ? 24 : 0
                visible: root.clash.length > 0
                radius: Theme.radiusSmall
                color: Qt.alpha(Theme.warn, 0.14)
                border.width: 1
                border.color: Qt.alpha(Theme.warn, 0.4)

                Text {
                    anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                    text: "taken from " + root.clash
                    color: Theme.warn
                    font.family: Theme.mono
                    font.pixelSize: 10
                }
            }

            ListView {
                anchors {
                    left: parent.left; right: parent.right
                    top: warning.bottom; topMargin: 8
                    bottom: parent.bottom
                }
                model: Keymap.actions.concat(Keymap.reserved)
                clip: true
                spacing: 2
                boundsBehavior: Flickable.StopAtBounds

                delegate: Item {
                    id: row
                    required property var modelData
                    width: ListView.view.width
                    height: 26

                    // A reserved row has its key written into it; a bindable one
                    // reads the map. That is also what makes it clickable.
                    readonly property bool fixed: row.modelData.key !== undefined
                    readonly property string spec: row.fixed ? row.modelData.key : Keymap.combo(row.modelData.id)

                    Rectangle {
                        anchors.fill: parent
                        radius: Theme.radiusSmall
                        color: rowHit.containsMouse && !row.fixed ? Theme.rail : "transparent"
                    }

                    Text {
                        anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                        width: parent.width - 120
                        text: row.modelData.label
                        color: row.fixed ? Theme.inkFaint : Theme.ink
                        font.family: Theme.ui
                        font.pixelSize: 12
                        elide: Text.ElideRight
                    }

                    Rectangle {
                        anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                        width: Math.max(shown.implicitWidth + 14, 44)
                        height: 20
                        radius: Theme.radiusSmall
                        color: root.capturing === row.modelData.id ? Qt.alpha(Theme.live, 0.18) : Theme.sunk
                        border.width: 1
                        border.color: root.capturing === row.modelData.id ? Theme.live : Theme.edge

                        Text {
                            id: shown
                            anchors.centerIn: parent
                            text: root.capturing === row.modelData.id
                                  ? "press…"
                                  : (row.spec.length > 0 ? row.spec.replace(/Cmd/g, "⌘").replace(/Ctrl/g, "⌃")
                                                                  .replace(/Shift/g, "⇧").replace(/Alt/g, "⌥")
                                                                  .replace(/\+/g, "")
                                                         : "—")
                            color: row.fixed ? Theme.inkFaint
                                             : (root.capturing === row.modelData.id ? Theme.live : Theme.inkDim)
                            font.family: Theme.mono
                            font.pixelSize: 10
                        }
                    }

                    MouseArea {
                        id: rowHit
                        anchors.fill: parent
                        hoverEnabled: true
                        onEntered: root.showSpec(row.spec)
                        onExited: root.hot = []
                        onClicked: {
                            if (row.fixed)
                                return;
                            root.clash = "";
                            root.capturing = root.capturing === row.modelData.id ? "" : row.modelData.id;
                        }
                    }
                }
            }
        }
    }

    // The whole panel listens, and it keeps every key it hears.
    //
    // Not only because a rebinding is a key pressed anywhere in it: a board you
    // are pressing keys at cannot also be letting those keys drive the scene
    // behind it — Space would play, I would mark in, and you would be told what
    // the key does by a timeline you cannot see. The shell's own shortcuts stand
    // down while this is open (Main.qml), and what is left lands here, lights
    // its caps and says what it does under the board.
    //
    // Escape is the one exception, because it is the way out.
    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_Escape) {
            if (root.capturing.length > 0)
                root.stopCapturing();
            else
                root.visible = false;
            event.accepted = true;
            return;
        }

        event.accepted = true;

        if (root.capturing.length === 0) {
            const mod = root.modifierToken(event.key);
            root.showSpec(mod.length > 0 ? mod : Keymap.comboFrom(event));
            return;
        }

        const spec = Keymap.comboFrom(event);
        if (spec.length === 0)
            return;

        root.clash = Keymap.holder(spec, root.capturing);
        // A key the system owns cannot be taken: the menu bar answers it before
        // the window ever sees it, so binding to it would do nothing at all.
        for (const one of Keymap.reserved) {
            if (one.key === spec) {
                root.capturing = "";
                return;
            }
        }
        Keymap.bind(root.capturing, spec);
        root.capturing = "";
    }

    onVisibleChanged: {
        if (visible) {
            forceActiveFocus();
        } else {
            stopCapturing();
            hot = [];
            struck = "";
        }
    }
}
