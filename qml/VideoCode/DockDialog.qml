// A question the dock has to ask before it does something you cannot undo.
//
// Centred and modal on purpose. Everything else in this chrome is a menu that
// closes when you look away, which is right for a choice you can take back by
// making it again — and wrong for one that throws away work: "Reset UI" forgets
// an arrangement you may have spent an afternoon on, and a stray click on a menu
// row should not be able to do that.
//
// One dialog serves both questions the dock asks, because they are the same
// shape: a sentence, sometimes a name to type, and up to three ways out.
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls

Item {
    id: root

    property string title: ""
    property string message: ""

    // A name to type, when the question needs one.
    property bool asksName: false
    property string placeholder: ""

    // The middle way out — "save it first", when there is one.
    property string extraLabel: ""

    property string acceptLabel: "OK"
    // Destructive answers wear the warning, never the warm accent, which in this
    // chrome means "this is live" and not "this is dangerous".
    property bool destructive: false

    signal accepted(string name)
    signal extraChosen()

    visible: false

    function ask() {
        visible = true;
        if (asksName) {
            field.text = "";
            field.forceActiveFocus();
        }
    }

    function close() {
        visible = false;
    }

    // The scrim is what makes it modal: it eats the click that would otherwise
    // reach the dock behind, and it dims what you are being asked about.
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.45)

        MouseArea {
            anchors.fill: parent
            // Clicking beside the dialog is the same as cancelling, but nothing
            // is decided by it — the destructive button is the only way through.
            onPressed: root.close()
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: 420
        height: card.height + 36
        color: Theme.panel
        border.color: Theme.edge
        border.width: 1
        radius: Theme.radius

        // Swallow clicks that land on the card, or the scrim below would close it.
        MouseArea { anchors.fill: parent }

        Column {
            id: card
            anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter }
            anchors.margins: 18
            spacing: 10

            Text {
                width: parent.width
                text: root.title
                color: Theme.ink
                font.family: Theme.ui
                font.pixelSize: 14
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }

            Text {
                width: parent.width
                visible: root.message.length > 0
                text: root.message
                color: Theme.inkDim
                font.family: Theme.ui
                font.pixelSize: 12
                lineHeight: 1.25
                wrapMode: Text.WordWrap
            }

            TextField {
                id: field
                visible: root.asksName
                width: parent.width
                placeholderText: root.placeholder
                color: Theme.ink
                font.family: Theme.ui
                font.pixelSize: 12
                background: Rectangle {
                    color: Theme.sunk
                    radius: Theme.radiusSmall
                    border.width: 1
                    border.color: field.activeFocus ? Theme.live : Theme.edge
                }
                onAccepted: {
                    if (field.text.trim().length > 0) {
                        root.close();
                        root.accepted(field.text.trim());
                    }
                }
            }

            Item { width: 1; height: 2 }

            Row {
                anchors.right: parent.right
                spacing: 8

                component Choice: Rectangle {
                    id: choice
                    property string label: ""
                    property bool primary: false
                    property bool enabledLook: true

                    signal chosen()

                    width: choiceLabel.implicitWidth + 26
                    height: 26
                    radius: Theme.radiusSmall
                    opacity: choice.enabledLook ? 1 : 0.4
                    color: !choice.primary
                           ? (choiceHover.hovered ? Theme.rail : "transparent")
                           : (root.destructive
                              ? Qt.alpha(Theme.bad, choiceHover.hovered ? 0.34 : 0.22)
                              : Qt.alpha(Theme.live, choiceHover.hovered ? 0.34 : 0.22))
                    border.width: 1
                    border.color: !choice.primary
                                  ? Theme.edge
                                  : (root.destructive ? Theme.bad : Theme.live)

                    Text {
                        id: choiceLabel
                        anchors.centerIn: parent
                        text: choice.label
                        color: !choice.primary
                               ? (choiceHover.hovered ? Theme.ink : Theme.inkDim)
                               : (root.destructive ? Theme.bad : Theme.live)
                        font.family: Theme.ui
                        font.pixelSize: 12
                    }

                    HoverHandler { id: choiceHover }
                    TapHandler {
                        enabled: choice.enabledLook
                        onTapped: choice.chosen()
                    }
                }

                Choice {
                    label: "Cancel"
                    onChosen: root.close()
                }

                Choice {
                    visible: root.extraLabel.length > 0
                    label: root.extraLabel
                    onChosen: {
                        root.close();
                        root.extraChosen();
                    }
                }

                Choice {
                    label: root.acceptLabel
                    primary: true
                    // A display with no name is not saved, it is lost.
                    enabledLook: !root.asksName || field.text.trim().length > 0
                    onChosen: {
                        root.close();
                        root.accepted(field.text.trim());
                    }
                }
            }
        }
    }
}
