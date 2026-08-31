// The board, and what it is bound to.
//
// A list of shortcuts tells you what exists; a KEYBOARD tells you where to put
// your hand, which is the actual question. Hover an action and the whole
// combination lights up — modifiers included, so there is no layer to switch to;
// hover a key and it says what it does.
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

    function light(id) {
        const spec = Keymap.combo(id);
        if (spec.length === 0) {
            root.hot = [];
            return;
        }
        root.hot = Keymap.modsOf(spec).concat([Keymap.baseOf(spec)]);
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
            Math.max(keyboard.height + 150,
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
            anchors { right: parent.right; rightMargin: 20; verticalCenter: title.verticalCenter }
            text: root.capturing.length > 0 ? "esc to cancel" : "esc"
            color: root.capturing.length > 0 ? Theme.live : Theme.inkFaint
            font.family: Theme.mono
            font.pixelSize: 10
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
                                    onEntered: legend.text = root.boundTo(cap.token)
                                    onExited: legend.text = ""
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

        Text {
            id: legend
            anchors {
                left: keyboard.left; right: keyboard.right
                top: sides.bottom; topMargin: 10
            }
            color: Theme.inkDim
            font.family: Theme.mono
            font.pixelSize: 11
            elide: Text.ElideRight
        }

        Text {
            anchors { left: keyboard.left; right: keyboard.right; top: legend.bottom; topMargin: 6 }
            // The second sentence is DERIVED, not written: it names the actions
            // Keymap says are qualified, so an action that gains or loses the
            // qualifier changes this line with it. The column beside the board
            // is too narrow to carry it per row — an ellipsis over a caveat is
            // not a caveat.
            text: {
                let qualified = [];
                for (const action of Keymap.actions)
                    if (action.only !== undefined)
                        qualified.push(action.label.toLowerCase());
                let line = "Hover an action to light the keys you press for it. "
                         + "Click its combination and press the new one.";
                if (qualified.length > 0)
                    line += "\n" + qualified.join(", ")
                          + " work " + Keymap.actions.find(a => a.only !== undefined).only
                          + " — while the caret is in it, those keys write.";
                return line;
            }
            color: Theme.inkFaint
            font.family: Theme.ui
            font.pixelSize: 11
            wrapMode: Text.Wrap
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
                        onEntered: root.light(row.fixed ? "" : row.modelData.id)
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

    // The whole panel listens, because a rebinding is a key pressed anywhere in
    // it — and because escape has to close the capture before it closes the
    // panel, or nobody can ever cancel one.
    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_Escape) {
            if (root.capturing.length > 0)
                root.stopCapturing();
            else
                root.visible = false;
            event.accepted = true;
            return;
        }

        if (root.capturing.length === 0)
            return;

        const spec = Keymap.comboFrom(event);
        event.accepted = true;
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
        }
    }
}
