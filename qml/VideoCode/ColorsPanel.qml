// The legend, and a hand on it.
//
// What the timeline paints, one row per hue: the swatch, what it means, the
// value as #RRGGBBAA, and the colour it shipped with. Click a swatch and a
// palette unfolds under it — a row of hues the theme already owns rather than a
// wheel, so a repainted timeline is still this product's timeline; the field
// takes anything else. The default is on every row whether or not it was
// changed: a way back that only shows up sometimes is one nobody finds.
//
// Writing goes through Theme.overrides and nowhere else, so the timeline
// repaints as the value lands and the file only ever holds what was changed.
pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: root
    anchors.fill: parent
    visible: false

    // { section } or { label, meaning }, in reading order.
    property var rows: []

    // An override was set or cleared; the shell writes the file.
    signal changed()

    // The label whose palette is unfolded, or "".
    property string open: ""

    // Every hue the theme already names, once each: the legend's own, the
    // effect complements, and the four the rest of the chrome speaks in.
    readonly property var hues: {
        const out = [];
        const add = (c) => { if (out.indexOf(c) < 0) out.push(c); };
        for (const label in Theme.shipped)
            add(Theme.shipped[label]);
        for (const kind in Theme.fxKind)
            add(Theme.fxKind[kind]);
        for (const c of [Theme.ai, Theme.warn, Theme.flaw, Theme.bad])
            add(String(c));
        return out;
    }

    function hex(c) {
        const two = (v) => ("0" + Math.round(v * 255).toString(16)).slice(-2);
        return "#" + two(c.r) + two(c.g) + two(c.b) + two(c.a);
    }

    // #RRGGBB or #RRGGBBAA, case-free; anything else is refused.
    function canonical(text) {
        const m = /^#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?$/.exec(text.trim());
        return m === null ? "" : ("#" + m[1] + (m[2] || "ff")).toLowerCase();
    }

    function set(label, value) {
        let next = Object.assign({}, Theme.overrides);
        if (value === "")
            delete next[label];
        else
            next[label] = value;
        Theme.overrides = next;
        root.changed();
    }

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.55)

        MouseArea {
            anchors.fill: parent
            onClicked: root.visible = false
        }
    }

    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(640, root.width - 80)
        height: Math.min(body.implicitHeight + 60, root.height - 60)
        color: Theme.panel
        radius: Theme.radius
        border.width: 1
        border.color: Theme.edge

        MouseArea { anchors.fill: parent }

        Text {
            id: title
            anchors { left: parent.left; leftMargin: 18; top: parent.top; topMargin: 16 }
            text: "Colors"
            color: Theme.ink
            font.family: Theme.ui
            font.pixelSize: 13
        }

        Text {
            anchors { right: parent.right; rightMargin: 18; verticalCenter: title.verticalCenter }
            text: "esc"
            color: Theme.inkFaint
            font.family: Theme.mono
            font.pixelSize: 10
        }

        Column {
            id: body
            anchors {
                left: parent.left; right: parent.right
                top: title.bottom; topMargin: 10
            }

            Repeater {
                model: root.rows

                Item {
                    id: row
                    required property var modelData
                    readonly property bool heading: row.modelData.section !== undefined
                    readonly property string label: row.heading ? "" : row.modelData.label
                    readonly property bool opened: !row.heading && root.open === row.label

                    // Coerced through a colour property so the hex is read off
                    // real channels, whichever form Theme wrote the value in.
                    readonly property color current: row.heading ? "transparent" : Theme.hue(row.label)
                    readonly property color shipped: row.heading ? "transparent" : Theme.shipped[row.label]
                    readonly property string currentHex: root.hex(row.current)
                    readonly property string shippedHex: root.hex(row.shipped)
                    readonly property bool changed: currentHex !== shippedHex

                    width: body.width
                    height: row.heading ? 30 : (row.opened ? 78 : 46)

                    function apply(text) {
                        const value = root.canonical(text);
                        if (value === "")
                            return;
                        root.set(row.label, value === row.shippedHex ? "" : value);
                    }

                    onCurrentHexChanged: if (!field.activeFocus) field.text = row.currentHex

                    Text {
                        visible: row.heading
                        anchors { left: parent.left; leftMargin: 18; bottom: parent.bottom; bottomMargin: 6 }
                        text: row.heading ? row.modelData.section.toUpperCase() : ""
                        color: Theme.inkFaint
                        font.family: Theme.ui
                        font.pixelSize: 10
                        font.letterSpacing: 0.8
                    }

                    // ── The swatch: what the timeline paints, at a size a hand can hit ──
                    Rectangle {
                        id: swatch
                        visible: !row.heading
                        anchors { left: parent.left; leftMargin: 18; top: parent.top; topMargin: 9 }
                        width: 28
                        height: 28
                        radius: Theme.radiusSmall
                        color: row.current
                        border.width: 1
                        border.color: row.opened || swatchHit.containsMouse ? Theme.ink : Theme.edge

                        MouseArea {
                            id: swatchHit
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: root.open = row.opened ? "" : row.label
                        }
                    }

                    Text {
                        id: name
                        visible: !row.heading
                        anchors { left: swatch.right; leftMargin: 12; top: parent.top; topMargin: 8 }
                        text: row.label
                        color: Theme.ink
                        font.family: Theme.ui
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                    }

                    Text {
                        visible: !row.heading
                        anchors { left: name.left; right: box.left; rightMargin: 12; top: name.bottom; topMargin: 1 }
                        text: row.heading ? "" : row.modelData.meaning
                        color: Theme.inkFaint
                        font.family: Theme.ui
                        font.pixelSize: 10
                        elide: Text.ElideRight
                    }

                    // ── The value, typed ──
                    Rectangle {
                        id: box
                        visible: !row.heading
                        anchors { right: fallback.left; rightMargin: 14; top: parent.top; topMargin: 12 }
                        width: 88
                        height: 22
                        radius: Theme.radiusSmall
                        color: Theme.sunk
                        border.width: 1
                        border.color: field.activeFocus ? Theme.live : Theme.edge

                        TextInput {
                            id: field
                            anchors { fill: parent; leftMargin: 7; rightMargin: 7 }
                            verticalAlignment: TextInput.AlignVCenter
                            text: row.currentHex
                            color: Theme.ink
                            selectionColor: Qt.alpha(Theme.live, 0.35)
                            font.family: Theme.mono
                            font.pixelSize: 10
                            maximumLength: 9
                            selectByMouse: true
                            // A valid value lands as it is typed; whatever is
                            // left when the caret leaves is put back to what
                            // the timeline actually shows.
                            onTextEdited: row.apply(text)
                            onEditingFinished: text = row.currentHex
                        }
                    }

                    // ── What it shipped as, and the way back ──
                    Item {
                        id: fallback
                        visible: !row.heading
                        anchors { right: parent.right; rightMargin: 18; top: parent.top; topMargin: 12 }
                        width: 128
                        height: 22

                        Rectangle {
                            anchors.fill: parent
                            radius: Theme.radiusSmall
                            color: row.changed && fallbackHit.containsMouse ? Theme.rail : "transparent"
                        }

                        Row {
                            anchors { left: parent.left; leftMargin: 6; verticalCenter: parent.verticalCenter }
                            spacing: 6

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: "default"
                                color: Theme.inkFaint
                                font.family: Theme.ui
                                font.pixelSize: 9
                            }

                            Rectangle {
                                anchors.verticalCenter: parent.verticalCenter
                                width: 12
                                height: 12
                                radius: 3
                                color: row.shipped
                                border.width: 1
                                border.color: Theme.edge
                            }

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: row.shippedHex
                                color: row.changed ? Theme.inkDim : Theme.inkFaint
                                font.family: Theme.mono
                                font.pixelSize: 10
                            }
                        }

                        MouseArea {
                            id: fallbackHit
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: row.changed ? Qt.PointingHandCursor : Qt.ArrowCursor
                            onClicked: if (row.changed) root.set(row.label, "")
                        }
                    }

                    // ── The palette, under the row it is for ──
                    // Placed by index rather than in a Row: a positioner lays
                    // out on the next polish, and a hidden window polishes only
                    // when it is grabbed — so a scripted click that followed
                    // the swatch's found every chip still stacked at x = 0.
                    Repeater {
                        model: row.opened ? root.hues : []

                        Rectangle {
                            id: choice
                            required property int index
                            required property string modelData
                            readonly property bool picked: root.hex(choice.color) === row.currentHex
                            x: name.x + choice.index * 24
                            y: 48
                            width: 20
                            height: 20
                            radius: Theme.radiusSmall
                            color: choice.modelData
                            border.width: choice.picked ? 2 : 1
                            border.color: choice.picked || choiceHit.containsMouse ? Theme.ink : Theme.edge

                            MouseArea {
                                id: choiceHit
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: row.apply(root.hex(choice.color))
                            }
                        }
                    }
                }
            }

            Item { width: 1; height: 8 }

            // Where the choices live, said out loud, for the same reason
            // Settings names the dock's file.
            Column {
                width: body.width
                spacing: 6

                Rectangle {
                    x: 18
                    width: body.width - 36
                    height: 1
                    color: Theme.edgeSoft
                }

                Text {
                    leftPadding: 18
                    rightPadding: 18
                    width: body.width
                    text: "What you change is kept in ~/Library/Preferences/video-code/colors.json — only the entries that differ from their default."
                    color: Theme.inkFaint
                    font.family: Theme.mono
                    font.pixelSize: 10
                    wrapMode: Text.Wrap
                }
            }
        }
    }

    Keys.onEscapePressed: root.visible = false

    // And again, matched by the window rather than by the focus chain.
    //
    // `Keys.onEscapePressed` only fires for the item holding active focus: the
    // moment a hex field is clicked the panel's root no longer has it, the key
    // goes to the field, which does nothing with it, and the panel stays open.
    // Every other overlay is dismissed before its fields are ever touched,
    // which is why this one is the first to need it.
    Shortcut {
        sequence: "Esc"
        enabled: root.visible
        onActivated: root.visible = false
    }
    onVisibleChanged: {
        if (visible)
            forceActiveFocus();
        else
            open = "";
    }
}
