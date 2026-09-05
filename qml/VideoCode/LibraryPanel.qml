// Everything a scene can be GIVEN, as opposed to what can be done to it.
//
// The effects library lives inside the element card, because an effect is
// always an effect ON something. A shape is not: it is a new line in the scene,
// and it needs no element selected and no card open. So it gets a panel of its
// own, dockable like the rest, and the gesture that places it is the one the
// effects taught — set the parameters first, then carry it to the moment you
// want it, because a template dropped and then configured is a template you
// have to find again.
//
// The catalogue is discovered, never listed here: an `Input` the library
// exposes is something a person could have typed, and nothing else is offered.
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls

Item {
    id: root

    // {name, group, module, says, params, required} — see Editor::templates.
    property var catalogue: []

    property string query: ""

    // What is being configured, and what its fields have been set to. `null`
    // until something is chosen: the list and the fields are the same panel at
    // two depths, not two panels.
    property var picked: null
    property var values: ({})

    // Carried across the window, in window coordinates, so whatever is under
    // the pointer can decide what a drop there means.
    signal carrying(var template, var values, real x, real y)
    signal dropped(var template, var values, real x, real y)
    signal released()

    readonly property var groups: [
        { key: "shape", label: "SHAPES" },
        { key: "media", label: "MEDIA" },
        { key: "template", label: "TEMPLATES" },
        // What the project's own templates/ folder holds — its own heading,
        // because "did I write this or did it ship?" is the first thing you ask
        // of a name you do not recognise.
        { key: "yours", label: "YOUR TEMPLATES" },
        { key: "effect", label: "EFFECTS" },
        { key: "interface", label: "INTERFACE" }
    ]

    // Fields with nothing in them and no default to fall back on. A `Text` with
    // no text is a call that raises, and the panel says so instead of writing it.
    readonly property var missing: {
        if (picked === null)
            return [];
        const out = [];
        for (const parameter of picked.params) {
            if (parameter.optional)
                continue;
            const written = values[parameter.name];
            if (written === undefined || String(written).trim().length === 0)
                out.push(parameter.name);
        }
        return out;
    }

    function matching(group) {
        const needle = query.trim().toLowerCase();
        const out = [];
        for (const one of catalogue) {
            if (one.group !== group)
                continue;
            if (needle.length > 0
                && one.name.toLowerCase().indexOf(needle) < 0
                && one.says.toLowerCase().indexOf(needle) < 0)
                continue;
            out.push(one);
        }
        return out;
    }

    function pick(template) {
        picked = template;
        // Defaults are what the signature says, and they are NOT written into
        // the call — see Main.placeTemplate. Kept here only so a field shows
        // what it will do if you leave it alone.
        const start = ({});
        for (const parameter of template.params)
            start[parameter.name] = parameter.value;
        values = start;
    }

    function dismiss() {
        picked = null;
        values = ({});
    }

    // ── The list ──────────────────────────────────────────────────────────
    Item {
        id: head
        anchors { left: parent.left; right: parent.right; top: parent.top }
        anchors.margins: 10
        height: 26
        visible: root.picked === null

        Rectangle {
            anchors.fill: parent
            radius: Theme.radiusSmall
            color: Theme.sunk
            border.width: 1
            border.color: search.activeFocus ? Theme.live : Theme.edge

            TextInput {
                id: search
                anchors { fill: parent; leftMargin: 9; rightMargin: 9 }
                verticalAlignment: TextInput.AlignVCenter
                color: Theme.ink
                font.family: Theme.mono
                font.pixelSize: 11
                selectByMouse: true
                onTextEdited: root.query = text
                Keys.onEscapePressed: { text = ""; root.query = ""; root.forceActiveFocus(); }
            }

            Text {
                anchors { left: parent.left; leftMargin: 9; verticalCenter: parent.verticalCenter }
                visible: search.text.length === 0
                text: "search " + root.catalogue.length + " things to place"
                color: Theme.inkFaint
                font.family: Theme.mono
                font.pixelSize: 11
            }
        }
    }

    ScrollView {
        anchors {
            left: parent.left; right: parent.right
            top: head.bottom; topMargin: 6
            bottom: parent.bottom
        }
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        clip: true
        visible: root.picked === null

        Column {
            width: root.width - 20
            spacing: 4
            bottomPadding: 10

            Repeater {
                model: root.groups

                Column {
                    id: family
                    required property var modelData
                    width: parent.width
                    spacing: 4
                    visible: rows.count > 0

                    Text {
                        text: family.modelData.label
                        color: Theme.inkFaint
                        font.family: Theme.ui
                        font.pixelSize: 10
                        font.weight: Font.DemiBold
                        font.letterSpacing: 0.9
                        topPadding: 8
                        bottomPadding: 2
                    }

                    Repeater {
                        id: rows
                        model: root.matching(family.modelData.key)

                        Rectangle {
                            id: row
                            required property var modelData
                            width: parent.width
                            height: 30
                            radius: Theme.radiusSmall
                            color: hover.containsMouse ? Qt.alpha(Theme.live, 0.10) : "transparent"
                            border.width: 1
                            border.color: hover.containsMouse ? Qt.alpha(Theme.live, 0.5) : "transparent"

                            Text {
                                id: rowName
                                anchors { left: parent.left; leftMargin: 9; verticalCenter: parent.verticalCenter }
                                text: row.modelData.name
                                // A file of yours the catalogue could not use is
                                // listed too, with the reason beside it. Left
                                // out, it reads as one you never wrote, and you
                                // go looking for it in the folder.
                                color: row.modelData.broken ? Theme.bad : Theme.ink
                                font.family: Theme.mono
                                font.pixelSize: 11
                            }

                            // What the class says about itself, when there is
                            // room for it. Never a description written here:
                            // two of them would drift apart.
                            Text {
                                anchors {
                                    left: rowName.right; leftMargin: 10
                                    right: parent.right; rightMargin: 9
                                    verticalCenter: parent.verticalCenter
                                }
                                visible: width > 60
                                text: row.modelData.says
                                color: row.modelData.broken ? Theme.bad : Theme.inkFaint
                                font.family: Theme.ui
                                font.pixelSize: 10
                                elide: Text.ElideRight
                                horizontalAlignment: Text.AlignRight
                            }

                            MouseArea {
                                id: hover
                                anchors.fill: parent
                                hoverEnabled: !row.modelData.broken
                                onClicked: if (!row.modelData.broken) root.pick(row.modelData)
                            }
                        }
                    }
                }
            }
        }
    }

    // ── One of them, with its fields ──────────────────────────────────────
    Item {
        id: chosen
        anchors.fill: parent
        anchors.margins: 10
        visible: root.picked !== null

        Text {
            id: chosenName
            anchors { left: parent.left; top: parent.top }
            text: root.picked !== null ? root.picked.name : ""
            color: Theme.ink
            font.family: Theme.mono
            font.pixelSize: 12
            font.weight: Font.DemiBold
        }

        Text {
            id: back
            anchors { right: parent.right; verticalCenter: chosenName.verticalCenter }
            text: "back"
            color: backTap.containsMouse ? Theme.live : Theme.inkDim
            font.family: Theme.ui
            font.pixelSize: 11

            MouseArea {
                id: backTap
                anchors.fill: parent
                anchors.margins: -6
                hoverEnabled: true
                onClicked: root.dismiss()
            }
        }

        Text {
            id: chosenSays
            anchors { left: parent.left; right: parent.right; top: chosenName.bottom; topMargin: 4 }
            text: root.picked !== null ? root.picked.says : ""
            color: Theme.inkFaint
            font.family: Theme.ui
            font.pixelSize: 10
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
        }

        ListView {
            id: fields
            anchors {
                left: parent.left; right: parent.right
                top: chosenSays.bottom; topMargin: 8
                bottom: carry.top; bottomMargin: 10
            }
            clip: true
            spacing: 6
            boundsBehavior: Flickable.StopAtBounds
            model: root.picked !== null ? root.picked.params : []

            delegate: Item {
                id: field
                required property var modelData
                width: ListView.view.width
                height: 26

                readonly property bool needed: !field.modelData.optional

                Text {
                    id: fieldName
                    anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                    width: Math.min(96, parent.width * 0.4)
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
                                  ? Theme.live
                                  : (field.needed && entry.text.trim().length === 0 ? Theme.bad : Theme.edge)

                    TextInput {
                        id: entry
                        anchors { fill: parent; leftMargin: 8; rightMargin: 8 }
                        verticalAlignment: TextInput.AlignVCenter
                        // Filled once, never bound: a field bound to the table
                        // it writes into is a loop, and Qt breaks it by dropping
                        // whichever half you did last.
                        Component.onCompleted: entry.text = root.values[field.modelData.name] !== undefined
                                               ? root.values[field.modelData.name] : field.modelData.value
                        color: Theme.ink
                        font.family: Theme.mono
                        font.pixelSize: 11
                        selectByMouse: true
                        Keys.onEscapePressed: root.forceActiveFocus()

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
                        visible: entry.text.trim().length === 0
                        text: field.modelData.kind
                        color: Theme.inkFaint
                        font.family: Theme.mono
                        font.pixelSize: 10
                    }
                }
            }
        }

        // The thing itself, picked up from here and carried to a moment on the
        // timeline. Dropped anywhere else it does nothing — a template that
        // lands wherever the caret happens to be is a line you did not place.
        Rectangle {
            id: carry
            anchors { left: parent.left; right: parent.right; bottom: hint.top; bottomMargin: 8 }
            height: 34
            radius: 4
            color: root.missing.length > 0 ? Theme.sunk : Theme.live
            border.width: 1
            border.color: root.missing.length > 0 ? Theme.edge : Theme.live

            Text {
                anchors.centerIn: parent
                text: root.picked === null
                      ? ""
                      : (root.missing.length > 0
                         ? root.missing.join(", ") + " — needed"
                         : (root.picked.group === "effect"
                            ? "drag " + root.picked.name + " onto a clip"
                            : "drag " + root.picked.name + " onto the timeline"))
                color: root.missing.length > 0 ? Theme.inkFaint : "#0b1018"
                font.family: Theme.mono
                font.pixelSize: 11
                font.weight: Font.DemiBold
            }

            MouseArea {
                anchors.fill: parent
                enabled: root.missing.length === 0
                cursorShape: enabled ? Qt.OpenHandCursor : Qt.ArrowCursor

                onPressed: (mouse) => {
                    const at = mapToItem(null, mouse.x, mouse.y);
                    root.carrying(root.picked, root.values, at.x, at.y);
                }
                onPositionChanged: (mouse) => {
                    if (!pressed)
                        return;
                    const at = mapToItem(null, mouse.x, mouse.y);
                    root.carrying(root.picked, root.values, at.x, at.y);
                }
                onReleased: (mouse) => {
                    const at = mapToItem(null, mouse.x, mouse.y);
                    root.dropped(root.picked, root.values, at.x, at.y);
                }
                onCanceled: root.released()
            }
        }

        Text {
            id: hint
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            text: root.picked !== null && root.picked.group === "effect"
                  ? "fields first, then the clip and the moment"
                  : "fields first, then the moment it should appear"
            color: Theme.inkFaint
            font.family: Theme.ui
            font.pixelSize: 10
            elide: Text.ElideRight
        }
    }

    Text {
        anchors.centerIn: parent
        visible: root.catalogue.length === 0
        text: "nothing to place — the library did not answer"
        color: Theme.inkFaint
        font.family: Theme.ui
        font.pixelSize: 11
    }
}
