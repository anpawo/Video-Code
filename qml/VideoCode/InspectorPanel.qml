// The clip you clicked, as rows in the dock.
//
// The shape is the one Palmier Pro and Final Cut share: a title strip, then
// sections that fold — a chevron and a name — and inside each, one row per
// value, its label on the left and its value in a field on the right. Nothing
// travels and nothing is drawn against a ruler: what a clip DOES over time is
// the flying card's business (a double-click); what it IS, and what its line
// says, is this panel's.
//
// Three sections. The line's own arguments, as written; the metadata calls the
// line adds (position, scale…), one row per field, with what can still be
// added; and what the element is worth at the playhead, read-only, since a
// value halfway through an effect is nobody's to type.
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls

Item {
    id: root

    property var element: null
    property string buffer: ""
    property real playhead: 0

    signal argumentWritten(var element, string call, string name, string value)
    signal metadataAdded(var element, string write)
    signal metadataWritten(var element, string call, string name, int at, string value)
    signal jumpRequested(var element)
    signal renamed(var element, string name)
    signal says(string sentence)

    // The same two entry points as the card, so the shell talks to both alike.
    function open(what, where) { element = what; }

    // The name just given, so the element is found again under it once the
    // scene has run: matched by index AND name, a renamed one would be lost.
    property string renamedTo: ""
    function follow(name) { renamedTo = name; }

    function rebind(elements) {
        if (element === null || element.index === undefined)
            return;
        const named = (one) => one.n === element.n || (renamedTo.length > 0 && one.n === renamedTo);
        for (const one of elements) {
            if (one.index === element.index && named(one)) {
                element = one;
                renamedTo = "";
                return;
            }
            for (const member of (one.members !== undefined ? one.members : [])) {
                if (member.index === element.index && member.n === element.n) {
                    element = member;
                    return;
                }
            }
        }
        element = null;
    }

    // ── What the line says ────────────────────────────────────────────────
    readonly property string cls: element !== null && element.cls !== undefined ? element.cls : ""
    readonly property string kind: element !== null && element.kind !== undefined ? element.kind : ""
    readonly property color hue: Theme.kind[kind] !== undefined ? Theme.kind[kind] : Theme.inkDim
    readonly property var arguments: cls.length > 0 ? Shell.inputParams(cls) : []
    readonly property bool writable: element !== null
                                     && element.line !== undefined && element.line > 0
                                     && cls.length > 0
                                     && Shell.callsOnLine(buffer, element.line).indexOf(cls) >= 0

    function written(name) {
        return root.writable ? Shell.readArgument(buffer, element.line, cls, name) : "";
    }
    function argOf(call, name) {
        return root.writable ? Shell.readArgument(buffer, element.line, call, name) : "";
    }
    function positionalOf(call, index) {
        return root.writable ? Shell.readPositional(buffer, element.line, call, index) : "";
    }
    // An enum typed by its short name is written in full: `WHITE` → `Color.WHITE`.
    function fullValue(param, text) {
        const typed = String(text).trim();
        const closed = typeof Shell.enumValues === "function" ? Shell.enumValues(param.kind) : [];
        for (const one of closed)
            if (one === typed || one.substring(one.lastIndexOf(".") + 1) === typed)
                return one;
        return typed;
    }
    function readable(value) {
        const rgba = String(value).match(/^\((\d+), *(\d+), *(\d+)(?:, *(\d+))?\)$/);
        if (rgba === null)
            return String(value);
        const hex = (n) => ("0" + Number(n).toString(16)).slice(-2);
        return "#" + hex(rgba[1]) + hex(rgba[2]) + hex(rgba[3])
                   + (rgba[4] !== undefined && Number(rgba[4]) !== 255 ? hex(rgba[4]) : "");
    }

    // ── What it is worth now ──────────────────────────────────────────────
    readonly property var meta: {
        if (root.element === null || root.element.index === undefined || typeof Shell.stateAt !== "function")
            return ({});
        return Shell.stateAt(root.element.index, Math.round(root.playhead * 30));
    }

    readonly property var argRows: root.arguments.map((one) => {
        const asWritten = root.written(one.name);
        const live = root.meta["Args:" + one.name];
        const shown = asWritten.length > 0 ? asWritten : one.value;
        const now = live !== undefined ? root.readable(live) : "";
        const isColor = /color/i.test(one.kind);
        const hex = now.startsWith("#") ? now : (/^"?#[0-9a-fA-F]{6}/.test(shown) ? shown.replace(/"/g, "") : "");
        return { label: one.name, param: one, value: shown, isDefault: asWritten.length === 0,
                 now: now !== shown && !isColor ? now : "", kind: one.kind,
                 swatch: isColor && hex.length > 0 ? hex.substring(0, 7) : "" };
    })

    // The metadata calls on the line: `.position(x=0, y=0)` is two rows.
    readonly property var metaRows: {
        if (root.element === null || root.element.effects === undefined)
            return [];
        const origin = root.element.l;
        let out = [];
        for (const fx of root.element.effects) {
            if (!(fx.d <= 1 / 30 + 1e-6 && fx.l <= origin + 1e-6))
                continue;
            const call = fx.call !== undefined ? fx.call : "";
            if (call.length === 0)
                continue;
            const fields = Shell.inputParams(root.cls + "." + call);
            fields.forEach((p, i) => {
                if (p.name === "offset" || p.name === "at")
                    return;
                const named = root.argOf(call, p.name);
                out.push({ label: fields.length > 1 ? call + " · " + p.name : call,
                           call: call, name: p.name, at: i, param: p,
                           value: named.length > 0 ? named : root.positionalOf(call, i) });
            });
        }
        return out;
    }

    readonly property var addable: {
        if (!root.writable)
            return [];
        const calls = [
            { name: "position", write: "position(x=0, y=0)" },
            { name: "scale", write: "scale(1)" },
            { name: "opacity", write: "opacity(255)" },
            { name: "align", write: "align(x=0.5, y=0.5)" }
        ];
        const already = Shell.callsOnLine(root.buffer, root.element.line);
        return calls.filter((one) => already.indexOf(one.name) < 0);
    }

    readonly property var nowRows: {
        const order = [
            ["Position X", "Position:x"], ["Position Y", "Position:y"],
            ["Scale X", "Scale:x"], ["Scale Y", "Scale:y"],
            ["Rotation", "Rotation"], ["Opacity", "Opacity"],
            ["Align X", "Align:x"], ["Align Y", "Align:y"]
        ];
        let out = [];
        for (const [label, key] of order)
            if (root.meta[key] !== undefined)
                out.push({ label: label, value: Number(root.meta[key]).toFixed(2) });
        return out;
    }

    // A value wears the colours the code pane gives it: a number, a string, a
    // NAME in capitals, a variable — so the Inspector and the buffer read alike.
    function painted(value) {
        const tok = Theme.code;
        const esc = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        const span = (t, c) => "<span style=\"color:" + c + "\">" + esc(t) + "</span>";
        let out = "";
        const re = /("[^"]*"|'[^']*'|\d+(?:\.\d+)?|[A-Za-z_][A-Za-z0-9_.]*|\s+|.)/g;
        let m;
        while ((m = re.exec(String(value))) !== null) {
            const t = m[0];
            if (/^["']/.test(t))
                out += span(t, tok.string);
            else if (/^\d/.test(t))
                out += span(t, tok.number);
            else if (/^[A-Za-z_]/.test(t))
                // A name is code: it wears the code pane's colour on a faint
                // pill, so it never reads as prose.
                out += "<span style=\"color:" + (/^[A-Z0-9_.]+$/.test(t.split(".").pop()) ? tok.caps : tok.variable)
                       + ";background-color:" + Theme.edge + "\">&nbsp;" + esc(t) + "&nbsp;</span>";
            else
                out += span(t, Theme.inkDim);
        }
        return out;
    }

    // Where a colour swatch sends its click: the chrome has no system picker
    // (this Qt ships without QtQuick.Dialogs), so the field takes the hex.
    QtObject {
        id: picker
        function ask(row, hex) { row.beginEdit(); }
    }

    Text {
        anchors.centerIn: parent
        visible: root.element === null
        text: "click a clip"
        color: Theme.inkFaint
        font.family: Theme.ui
        font.pixelSize: 12
    }

    // ── One row: a label, a value — a field only when the pointer is on it ──
    component FieldRow: Item {
        id: row
        property string label: ""
        property string value: ""
        // Grey when the value is only the default the class would use anyway.
        property bool faint: false
        // What the playhead reads, when an effect has moved it off the line.
        property string now: ""
        property bool editable: true
        property bool last: false
        // The type the line expects, shown while the pointer is on the row.
        property string kind: ""
        // A colour's own colour, as a swatch that opens the picker; "" for none.
        property string swatch: ""
        signal committed(string text)
        function beginEdit() { field.forceActiveFocus(); field.selectAll(); }

        width: parent !== null ? parent.width : 0
        height: 34

        // A MouseArea, not a TapHandler: under the slot's floor a handler never
        // sees the press (AgentPanel.qml says why). Pressing puts the caret in
        // the field with the value selected, ready to be overwritten.
        MouseArea {
            id: over
            anchors.fill: parent
            // Above the field: a press that reaches the TextInput first is lost
            // on its way through the Flickable; taken here, it lands.
            z: 2
            hoverEnabled: true
            cursorShape: row.editable ? Qt.PointingHandCursor : Qt.ArrowCursor
            onPressed: (mouse) => {
                if (!row.editable) { mouse.accepted = false; return; }
                row.beginEdit();
            }
            readonly property bool hovered: containsMouse
        }

        Text {
            id: labelText
            anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
            width: Math.min(implicitWidth, Math.max(40, parent.width - box.width - nowText.width - 36))
            text: row.label
            color: Theme.ink
            font.family: Theme.ui
            font.pixelSize: 12
            elide: Text.ElideRight
        }

        Text {
            anchors { left: labelText.right; leftMargin: 8; verticalCenter: parent.verticalCenter }
            visible: over.containsMouse && row.kind.length > 0
            text: row.kind
            color: Theme.inkFaint
            font.family: Theme.mono
            font.pixelSize: 10
        }

        Rectangle {
            id: dab
            anchors { right: box.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
            visible: row.swatch.length > 0
            width: 14; height: 14; radius: 4
            color: row.swatch.length > 0 ? row.swatch : "transparent"
            border.width: 1
            border.color: Qt.rgba(1, 1, 1, 0.25)
        }

        Text {
            id: nowText
            anchors { right: dab.visible ? dab.left : box.left; rightMargin: 8; verticalCenter: parent.verticalCenter }
            visible: row.now.length > 0
            width: visible ? implicitWidth : 0
            text: row.now
            color: Theme.inkFaint
            font.family: Theme.mono
            font.pixelSize: 10
        }

        // The value reads as text; the field around it only shows itself when
        // the pointer is there, the way a Settings row keeps its calm.
        Rectangle {
            id: box
            anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
            width: Math.min(150, Math.max(64, row.width * 0.42))
            height: 24
            radius: 6
            readonly property bool lit: row.editable && (over.hovered || field.activeFocus)
            color: lit ? Theme.sunk : "transparent"
            border.width: 1
            border.color: field.activeFocus ? Theme.live : lit ? Theme.edge : "transparent"

            // The coloured reading, under a field that only shows its own text
            // while it is being written in.
            Text {
                anchors { fill: parent; leftMargin: 8; rightMargin: 8 }
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignRight
                visible: !field.activeFocus
                opacity: row.faint ? 0.6 : 1
                textFormat: Text.RichText
                text: root.painted(row.value)
                      + (row.kind === "percent" ? "<span style=\"color:" + Theme.inkFaint + "\">%</span>" : "")
                font.family: Theme.mono
                font.pixelSize: 11
                elide: Text.ElideLeft
            }

            TextInput {
                id: field
                z: 1
                anchors { fill: parent; leftMargin: 8; rightMargin: 8 }
                verticalAlignment: TextInput.AlignVCenter
                horizontalAlignment: TextInput.AlignRight
                text: row.value
                color: activeFocus ? Theme.ink : "transparent"
                font.family: Theme.mono
                font.pixelSize: 11
                selectByMouse: true
                readOnly: !row.editable
                clip: true
                onAccepted: {
                    if (text !== row.value)
                        row.committed(text);
                    focus = false;
                }
                // Left without Enter: back to what the file says.
                onActiveFocusChanged: if (!activeFocus) text = Qt.binding(() => row.value)
            }
        }

        Rectangle {
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 14 }
            height: 1
            visible: !row.last
            color: Theme.edgeSoft
        }
    }

    // ── A section: a small title, then its rows in one rounded group ──────
    component Section: Column {
        id: section
        property string title: ""
        property string aside: ""
        property bool open: true
        default property alias rows: body.data
        width: parent !== null ? parent.width : 0
        spacing: 6
        topPadding: 14

        Item {
            width: parent.width
            height: 16

            Text {
                anchors { left: parent.left; leftMargin: 22; verticalCenter: parent.verticalCenter }
                text: section.title
                color: Theme.inkDim
                font.family: Theme.ui
                font.pixelSize: 11
                font.weight: Font.DemiBold
            }

            Row {
                anchors { right: parent.right; rightMargin: 22; verticalCenter: parent.verticalCenter }
                spacing: 8
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: section.aside
                    color: Theme.inkFaint
                    font.family: Theme.mono
                    font.pixelSize: 10
                }
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: section.open ? "▾" : "▸"
                    color: Theme.inkFaint
                    font.pixelSize: 10
                }
            }

            MouseArea { anchors.fill: parent; onClicked: section.open = !section.open }
        }

        Rectangle {
            x: 12
            width: parent.width - 24
            height: body.height
            visible: section.open
            radius: 10
            color: Theme.rail
            border.width: 1
            border.color: Theme.edgeSoft
            clip: true

            Column {
                id: body
                width: parent.width
            }
        }
    }

    // A bare Flickable, as the timeline has: inside a Controls ScrollView the
    // rows never received a press under the slot's floor.
    Flickable {
        anchors.fill: parent
        visible: root.element !== null
        clip: true
        contentWidth: width
        contentHeight: sheet.height
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}

        Column {
            id: sheet
            width: root.width
            bottomPadding: 16

            // ── The header card: what it is ───────────────────────────────
            Item {
                width: parent.width
                height: 76

                Rectangle {
                    x: 12; y: 12
                    width: parent.width - 24
                    height: 56
                    radius: 10
                    color: Theme.rail
                    border.width: 1
                    border.color: Theme.edgeSoft

                    Rectangle {
                        id: dot
                        anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
                        width: 26; height: 26; radius: 7
                        color: Qt.alpha(root.hue, 0.25)
                        border.width: 1
                        border.color: Qt.alpha(root.hue, 0.6)
                        Rectangle { anchors.centerIn: parent; width: 10; height: 10; radius: 3; color: root.hue }
                    }

                    // The name is a field: Enter renames it everywhere, here.
                    Rectangle {
                        id: nameText
                        anchors { left: dot.right; leftMargin: 6; top: parent.top; topMargin: 7 }
                        width: Math.min(nameField.implicitWidth + 16, parent.width - 130)
                        height: 22
                        radius: 5
                        readonly property bool lit: nameOver.hovered || nameField.activeFocus
                        color: lit ? Theme.sunk : "transparent"
                        border.width: 1
                        border.color: nameField.activeFocus ? Theme.live : lit ? Theme.edge : "transparent"
                        MouseArea {
                            id: nameOver
                            anchors.fill: parent
                            z: 2
                            hoverEnabled: true
                            cursorShape: Qt.IBeamCursor
                            onPressed: { nameField.forceActiveFocus(); nameField.selectAll(); }
                            readonly property bool hovered: containsMouse
                        }

                        TextInput {
                            id: nameField
                            z: 1
                            anchors { fill: parent; leftMargin: 4; rightMargin: 4 }
                            verticalAlignment: TextInput.AlignVCenter
                            text: root.element !== null && root.element.n !== undefined ? root.element.n : ""
                            color: Theme.ink
                            font.family: Theme.ui
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            selectByMouse: true
                            clip: true
                            validator: RegularExpressionValidator { regularExpression: /[A-Za-z_][A-Za-z0-9_]*/ }
                            onAccepted: {
                                if (root.element !== null && text !== root.element.n)
                                    root.renamed(root.element, text);
                                focus = false;
                            }
                            onActiveFocusChanged: if (!activeFocus) text = Qt.binding(() => root.element !== null && root.element.n !== undefined ? root.element.n : "")
                        }
                    }

                    Text {
                        anchors { left: dot.right; leftMargin: 10; top: nameText.bottom; topMargin: 1 }
                        text: root.cls + (root.element !== null && root.element.d > 0 ? "  ·  " + root.element.d.toFixed(1) + "s" : "")
                        color: Theme.inkFaint
                        font.family: Theme.ui
                        font.pixelSize: 11
                    }

                    Text {
                        anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                        text: root.element !== null && root.element.line > 0 ? "line " + root.element.line + "  ›" : ""
                        color: jump.hovered ? Theme.live : Theme.inkDim
                        font.family: Theme.ui
                        font.pixelSize: 11
                        MouseArea {
                            id: jump
                            anchors.fill: parent
                            anchors.margins: -6
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.jumpRequested(root.element)
                            readonly property bool hovered: containsMouse
                        }
                    }
                }
            }

            Section {
                title: "Arguments"
                aside: root.writable ? "" : "read only"

                Repeater {
                    model: root.argRows
                    FieldRow {
                        required property var modelData
                        required property int index
                        last: index === root.argRows.length - 1
                        label: modelData.label
                        value: modelData.value
                        faint: modelData.isDefault
                        now: modelData.now
                        kind: modelData.kind
                        swatch: modelData.swatch
                        editable: root.writable
                        onCommitted: (text) => root.argumentWritten(root.element, root.cls, modelData.label,
                                                                    root.fullValue(modelData.param, text))
                    }
                }
            }

            Section {
                title: "Transform"
                visible: root.metaRows.length > 0 || root.addable.length > 0

                Repeater {
                    model: root.metaRows
                    FieldRow {
                        required property var modelData
                        required property int index
                        last: index === root.metaRows.length - 1 && root.addable.length === 0
                        label: modelData.label
                        value: modelData.value
                        kind: modelData.param.kind
                        onCommitted: (text) => root.metadataWritten(root.element, modelData.call, modelData.name,
                                                                    modelData.at, root.fullValue(modelData.param, text))
                    }
                }

                // What the line does not set yet, one chip each: Palmier's "Add".
                Flow {
                    width: parent.width - 28
                    x: 14
                    spacing: 6
                    visible: root.addable.length > 0
                    topPadding: 8
                    bottomPadding: 8

                    Repeater {
                        model: root.addable
                        Rectangle {
                            required property var modelData
                            width: plus.implicitWidth + 16
                            height: 20
                            radius: 4
                            color: addHover.hovered ? Qt.alpha(Theme.live, 0.15) : Theme.rail
                            border.width: 1
                            border.color: addHover.hovered ? Theme.live : Theme.edge
                            Text {
                                id: plus
                                anchors.centerIn: parent
                                text: "+ " + parent.modelData.name
                                color: addHover.hovered ? Theme.live : Theme.inkDim
                                font.family: Theme.mono
                                font.pixelSize: 10
                            }
                            MouseArea {
                                id: addHover
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.metadataAdded(root.element, parent.modelData.write)
                                readonly property bool hovered: containsMouse
                            }
                        }
                    }
                }
            }

            Section {
                title: "At the playhead"
                aside: root.playhead.toFixed(2) + "s"
                visible: root.nowRows.length > 0

                Repeater {
                    model: root.nowRows
                    FieldRow {
                        required property var modelData
                        required property int index
                        last: index === root.nowRows.length - 1
                        label: modelData.label
                        value: modelData.value
                        editable: false
                        faint: true
                    }
                }
            }
        }
    }
}
