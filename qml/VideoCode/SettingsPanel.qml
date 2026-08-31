// What there is to set, which is deliberately not much.
//
// A setting exists here only when the answer genuinely differs between people —
// which colours you read code in, whether a bin shows pictures or names. Every
// other choice this application makes is either obvious from what you are doing
// or belongs to the arrangement, and arrangements are changed by dragging them,
// not by a panel of switches.
pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: root
    anchors.fill: parent
    visible: false

    // Chosen by the shell, applied by the shell: this panel only ever says what
    // was picked, so nothing here needs to know what a dock or a highlighter is.
    signal codeThemePicked(string key)
    signal mediaDisplayPicked(string key)
    signal resetRequested()

    property string mediaDisplay: "grid"

    readonly property var themeKeys: Object.keys(Theme.codeThemes)

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.55)

        MouseArea {
            anchors.fill: parent
            onClicked: root.visible = false
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: Math.min(460, root.width - 80)
        height: body.implicitHeight + 60
        color: Theme.panel
        radius: Theme.radius
        border.width: 1
        border.color: Theme.edge

        MouseArea { anchors.fill: parent }

        Text {
            id: title
            anchors { left: parent.left; leftMargin: 18; top: parent.top; topMargin: 16 }
            text: "Settings"
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
                top: title.bottom; topMargin: 14
            }
            spacing: 16

            Column {
                width: body.width
                spacing: 4

                Text {
                    leftPadding: 18
                    text: "CODE THEME"
                    color: Theme.inkFaint
                    font.family: Theme.ui
                    font.pixelSize: 10
                    font.letterSpacing: 0.8
                }

                Repeater {
                    model: root.themeKeys

                    Item {
                        id: themeRow
                        required property string modelData
                        width: body.width
                        height: 26

                        Rectangle {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            radius: Theme.radiusSmall
                            color: themeHit.containsMouse ? Theme.rail : "transparent"
                        }

                        // The palette itself is the label that matters: three
                        // swatches say more about a theme than its name does.
                        Row {
                            anchors { left: parent.left; leftMargin: 18; verticalCenter: parent.verticalCenter }
                            spacing: 8

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                width: 12
                                text: Theme.codeTheme === themeRow.modelData ? "✓" : ""
                                color: Theme.ok
                                font.family: Theme.mono
                                font.pixelSize: 11
                            }

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: Theme.codeThemes[themeRow.modelData].label
                                color: Theme.ink
                                font.family: Theme.ui
                                font.pixelSize: 12
                            }
                        }

                        Row {
                            anchors { right: parent.right; rightMargin: 20; verticalCenter: parent.verticalCenter }
                            spacing: 4

                            Repeater {
                                model: ["keyword", "string", "call", "comment"]

                                Rectangle {
                                    id: swatch
                                    required property string modelData
                                    width: 12; height: 12
                                    radius: 3
                                    color: Theme.codeThemes[themeRow.modelData].tokens[swatch.modelData]
                                }
                            }
                        }

                        MouseArea {
                            id: themeHit
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: root.codeThemePicked(themeRow.modelData)
                        }
                    }
                }
            }

            Column {
                width: body.width
                spacing: 4

                Text {
                    leftPadding: 18
                    text: "MEDIA"
                    color: Theme.inkFaint
                    font.family: Theme.ui
                    font.pixelSize: 10
                    font.letterSpacing: 0.8
                }

                Repeater {
                    model: [{ key: "grid", label: "Icons" }, { key: "list", label: "Details" }]

                    Item {
                        id: mediaRow
                        required property var modelData
                        width: body.width
                        height: 26

                        Rectangle {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            radius: Theme.radiusSmall
                            color: mediaHit.containsMouse ? Theme.rail : "transparent"
                        }

                        Row {
                            anchors { left: parent.left; leftMargin: 18; verticalCenter: parent.verticalCenter }
                            spacing: 8

                            Text {
                                width: 12
                                text: root.mediaDisplay === mediaRow.modelData.key ? "✓" : ""
                                color: Theme.ok
                                font.family: Theme.mono
                                font.pixelSize: 11
                            }

                            Text {
                                text: mediaRow.modelData.label
                                color: Theme.ink
                                font.family: Theme.ui
                                font.pixelSize: 12
                            }
                        }

                        MouseArea {
                            id: mediaHit
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: root.mediaDisplayPicked(mediaRow.modelData.key)
                        }
                    }
                }
            }

            // Where the arrangement lives, said out loud: a layout that outlives
            // the process has a file, and hiding which one is how a person ends
            // up unable to fix it when it goes wrong.
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
                    text: "The dock is kept in ~/Library/Preferences/video-code/dock.json"
                    color: Theme.inkFaint
                    font.family: Theme.mono
                    font.pixelSize: 10
                    wrapMode: Text.Wrap
                }

                Item {
                    width: body.width
                    height: 26

                    Rectangle {
                        anchors { left: parent.left; leftMargin: 18; verticalCenter: parent.verticalCenter }
                        width: reset.implicitWidth + 20
                        height: 22
                        radius: Theme.radiusSmall
                        color: resetHit.containsMouse ? Theme.rail : Theme.sunk
                        border.width: 1
                        border.color: Theme.edge

                        Text {
                            id: reset
                            anchors.centerIn: parent
                            text: "Reset this display"
                            color: Theme.warn
                            font.family: Theme.ui
                            font.pixelSize: 11
                        }

                        MouseArea {
                            id: resetHit
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                root.visible = false;
                                root.resetRequested();
                            }
                        }
                    }
                }
            }
        }
    }

    Keys.onEscapePressed: root.visible = false
    onVisibleChanged: if (visible) forceActiveFocus()
}
