// The board, and what it is bound to.
//
// A list of shortcuts tells you what exists; a KEYBOARD tells you where to put
// your hand, which is the actual question. Press a key and the whole
// combination lights up — modifiers included, so there is no layer to switch to
// — and, while you hold it, so does every action that uses it. Pointing at an
// action lights its keys — that is asking where a key is. Pointing at a CAP says
// nothing: the board answers a keyboard, not a mouse.
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

    // The combination the board is showing. Set by a key you press, or by an
    // action you point at, and it STAYS there until something else replaces it.
    property string struck: ""

    // The keys held down right now — pressed, not pointed at. Every action whose
    // own combination holds all of them lights up, so holding ⌘ shows everything
    // ⌘ is part of, and letting go puts them out.
    property var keysStruck: []

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
         ["N", "N"], ["M", "M"], [",", ","], [".", "."], ["/", "/"], ["⇧", "Shift", 2.5, "modR"]],
        [["⌃", "Ctrl", 1.5, "mod"], ["⌥", "Alt", 1.5, "mod"], ["⌘", "Cmd", 1.5, "mod"],
         ["space", "Space", 6], ["⌘", "Cmd", 1.5, "modR"], ["⌥", "Alt", 1.5, "modR"],
         ["←", "←"], ["↑", "↑"], ["↓", "↓"], ["→", "→"]]
    ]

    // Les volets du dock, donnés par la coquille : c'est elle qui les connaît,
    // et un volet ajouté demain doit avoir son onglet ici sans qu'on y pense.
    property var docks: []

    // À quel volet une action appartient : celui qui doit être sélectionné pour
    // qu'elle agisse. Aucun, c'est une touche globale — elle marche où qu'on soit.
    //
    // Lu sur `where`, qui existait déjà, plutôt que sur un deuxième champ à
    // tenir d'accord avec lui : Code est le volet de code ; Transport, ce sont
    // la tête de lecture et la plage, qui vivent sur la timeline ; le reste —
    // exécuter la scène, les touches que la barre de menus possède — n'attend
    // aucun volet.
    function dockOf(action) {
        if (action.where === "Code")
            return "code";
        if (action.where === "Transport")
            return "timeline";
        return "";
    }

    // Les familles : tout, les touches globales, puis un onglet par volet.
    readonly property var groups: {
        let out = [
            { id: "all",    label: "all",    holds: function (action) { return true; } },
            { id: "global", label: "global", holds: function (action) { return root.dockOf(action) === ""; } }
        ];
        for (const dock of root.docks) {
            const key = dock.id;
            out.push({ id: key, label: dock.label.toLowerCase(),
                       holds: function (action) { return root.dockOf(action) === key; } });
        }
        return out;
    }
    property string group: "all"

    function livesHere(action) {
        for (const one of root.groups)
            if (one.id === root.group)
                return one.holds(action);
        return true;
    }

    // Les deux familles, séparées par un blanc : celles qu'on peut relier, et
    // celles que la barre de menus possède — grises, et qui ne répondront pas
    // à un clic. Le blanc est un objet de la liste plutôt qu'une deuxième
    // grille : un seul flux garde les quatre colonnes alignées de part et
    // d'autre, et une famille vide ne laisse pas un trou derrière elle.
    readonly property var shown: {
        const mine = Keymap.actions.filter(root.livesHere);
        const theirs = Keymap.reserved.filter(root.livesHere);
        if (mine.length === 0 || theirs.length === 0)
            return mine.concat(theirs);
        return mine.concat([{ gap: true, id: "", label: "" }], theirs);
    }

    readonly property var held: ["Cmd", "Ctrl", "Shift", "Alt"]

    // ── The two ⌘ keys are two keys ───────────────────────────────────────
    // Qt cannot tell them apart — `Qt.AltModifier` means "an Alt key" — but
    // macOS reports the side beside the ordinary flags and the shell reads it
    // off every event. Lighting BOTH caps was the board claiming a keyboard has
    // one ⌘ in two places; the one under your thumb is the one that answered.
    //
    // Left and right bits, in the order the shell packs them.
    readonly property var sideBits: ({
        "Cmd":   [1 << 0, 1 << 1], "Alt":  [1 << 2, 1 << 3],
        "Shift": [1 << 4, 1 << 5], "Ctrl": [1 << 6, 1 << 7]
    })

    // Split in two so the rule can be checked without a keyboard: the bits come
    // from `nativeModifiers()`, which a synthesised key event does not carry, so
    // nothing about the sides is reachable from a scripted run otherwise.
    function sideLit(bits, token, right) {
        const pair = root.sideBits[token];
        if (pair === undefined)
            return true;
        // Nothing of that modifier is physically down, so the card is
        // describing a BINDING — and a binding is shown on the LEFT key. The
        // two ⌘ are two keys; lighting both said "either", which reads as one
        // key drawn twice. The left one is where a shortcut is written and
        // where a hand goes without being asked.
        if ((bits & (pair[0] | pair[1])) === 0)
            return !right;
        return (bits & pair[right ? 1 : 0]) !== 0;
    }

    // The bits AS THEY WERE when the key was struck, not as they are now.
    //
    // Reading them live lit the other ⌘ the instant you let go of the one you
    // were holding: with nothing down any more the rule falls back to "this is
    // a binding, and a binding names no side", and both caps came on. The card
    // is describing a key you pressed, so the answer is frozen at the press.
    property int sidesAt: 0

    function sideDown(token, right) {
        return root.sideLit(root.sidesAt, token, right);
    }

    // The modifiers a key event says are down, as tokens, leaving out `except`.
    // A released modifier is left out by name because platforms disagree on
    // whether its own release still carries its flag.
    function heldIn(modifiers, except) {
        return root.held.filter((token) => token !== except && (modifiers & Keymap.flagFor(token)) !== 0);
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

    // What the board is answering for, and which sides were down when it was
    // asked. Two ways in, and they differ only in that second number:
    //
    //   a key you PRESSED   — the very cap under your hand lights, and no other
    //   a row you POINT AT  — that is a binding, and ⌘S names no side, so both
    //
    // Pointing at a CAP is not one of them. The drawing of a keyboard answers a
    // keyboard; a picture that lit up under the pointer was answering the wrong
    // hand. Pointing at an action is a different gesture — it is asking where a
    // thing is, which is the whole reason there is a keyboard drawn here.
    function showSpec(spec, sides) {
        if (spec.length === 0)
            return;
        root.sidesAt = sides;
        root.struck = spec;
        root.hot = root.held.indexOf(spec) >= 0
                   ? [spec]
                   : Keymap.modsOf(spec).concat([Keymap.baseOf(spec)]);
    }

    // Survoler une pastille est un APERÇU, pas une frappe.
    //
    // La carte gardait la dernière survolée quand le pointeur était reparti
    // ailleurs : elle décrivait alors une action que plus rien à l'écran ne
    // désignait. En quittant, on revient à ce qui était là avant — la dernière
    // touche pressée, ou l'invitation quand il n'y en a pas eu.
    property string pressed: ""

    function previewSpec(spec) {
        if (root.pressed.length === 0)
            root.pressed = root.struck;
        root.showSpec(spec, 0);
    }

    function endPreview() {
        if (root.pressed.length === 0 && root.struck.length === 0)
            return;
        const back = root.pressed;
        root.pressed = "";
        root.struck = "";
        root.hot = [];
        if (back.length > 0)
            root.showSpec(back, 0);
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
            Math.max(keyboard.height + 96,
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
                right: parent.right; rightMargin: 20
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
                                readonly property bool held: cap.modelData.length > 3
                                readonly property bool rightHand: cap.held && cap.modelData[3] === "modR"
                                readonly property bool lit: root.hot.indexOf(cap.token) >= 0
                                                            && root.sideDown(cap.token, cap.rightHand)

                                width: line.unit * cap.units
                                height: 30
                                radius: Theme.radiusSmall
                                color: cap.lit ? Qt.alpha(Theme.live, 0.22) : Theme.sunk
                                border.width: 1
                                border.color: cap.lit ? Theme.live : Theme.edge

                                Text {
                                    anchors.centerIn: parent
                                    text: cap.modelData[0]
                                    color: cap.lit ? Theme.live : (cap.held ? Theme.inkFaint : Theme.inkDim)
                                    font.family: Theme.mono
                                    font.pixelSize: cap.modelData[0].length > 2 ? 9 : 11
                                }

                            }
                        }
                    }
                }
            }
        }

        // ── The actions ───────────────────────────────────────────────────
        // Sous le clavier, pas à côté : la question qu'on se pose devant cette
        // planche est « où j'appuie », et la réponse est le dessin. La liste est
        // ce qu'on lit ensuite, donc elle vient après, en largeur.
        //
        // Et en pastilles à la taille de leur nom : une rangée pleine largeur
        // par action donnait trente lignes de vide à droite, et il fallait
        // descendre pour lire ce qui tenait en trois colonnes.
        Item {
            id: actions
            anchors {
                left: keyboard.left; right: keyboard.right
                top: keyboard.bottom; topMargin: 18
                bottom: parent.bottom; bottomMargin: 18
            }

            Text {
                id: head
                anchors { left: parent.left; top: parent.top }
                text: "ACTIONS"
                color: Theme.inkFaint
                font.family: Theme.ui
                font.pixelSize: 10
                font.letterSpacing: 0.8
            }

            // Le filtre. Deux familles aujourd'hui ; la barre se remplira toute
            // seule quand `groups` en portera d'autres.
            Row {
                id: filters
                anchors { left: head.right; leftMargin: 14; verticalCenter: head.verticalCenter }
                spacing: 6

                Repeater {
                    model: root.groups

                    Rectangle {
                        id: tab
                        required property var modelData
                        readonly property bool on: root.group === tab.modelData.id
                        width: tabText.implicitWidth + 20
                        height: 22
                        radius: Theme.radiusSmall
                        color: tab.on ? Qt.alpha(Theme.live, 0.16) : Theme.sunk
                        border.width: 1
                        border.color: tab.on ? Theme.live : Theme.edge

                        Text {
                            id: tabText
                            anchors.centerIn: parent
                            text: tab.modelData.label
                            color: tab.on ? Theme.live : Theme.ink
                            font.family: Theme.ui
                            font.pixelSize: 13
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.group = tab.modelData.id
                        }
                    }
                }
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

            // Un volet sans touche à lui n'est pas un volet sans clavier : ce
            // sont les touches globales qui y répondent, et le dire vaut mieux
            // qu'une liste vide qui laisse croire que rien ne marche.
            Text {
                anchors { left: parent.left; top: warning.bottom; topMargin: 12 }
                visible: root.shown.length === 0
                text: "No keys of its own — the global keys apply here."
                color: Theme.ink
                font.family: Theme.ui
                font.pixelSize: 13
            }

            Flickable {
                anchors {
                    left: parent.left; right: parent.right
                    top: warning.bottom; topMargin: 8
                    bottom: parent.bottom
                }
                clip: true
                contentWidth: width
                contentHeight: grid.implicitHeight
                boundsBehavior: Flickable.StopAtBounds

                Flow {
                    id: grid
                    width: parent.width
                    spacing: 6

                    Repeater {
                        model: root.shown

                        Rectangle {
                            id: chipItem
                            required property var modelData

                            // Une ligne réservée porte sa touche ; une liaison la
                            // lit dans la carte, et c'est ce qui la rend cliquable.
                            readonly property bool gap: chipItem.modelData.gap === true
                            // Découpé une fois par liaison, pas à chaque lecture :
                            // `split` rend un tableau NEUF à chaque évaluation, et
                            // un Repeater nourri d'un tableau neuf détruit et
                            // refait ses cases sans arrêt.
                            readonly property var parts: chipItem.spec.length > 0 ? chipItem.spec.split("+") : []
                            readonly property bool fixed: chipItem.modelData.key !== undefined
                            readonly property string spec: chipItem.fixed
                                                           ? chipItem.modelData.key
                                                           : Keymap.combo(chipItem.modelData.id)
                            readonly property bool lit: !chipItem.gap && root.keysStruck.length > 0
                                                        && root.keysStruck.every((k) => chipItem.parts.indexOf(k) >= 0)

                            // Toutes la même largeur, un quart de la rangée :
                            // quatre colonnes qui s'alignent se parcourent d'un
                            // regard, là où des pastilles à la taille de leur
                            // nom faisaient un mur en dents de scie.
                            // Toute la largeur : dans un Flow, c'est ce qui casse
                            // la ligne, et sa hauteur EST l'écart entre les deux
                            // familles.
                            width: chipItem.gap ? grid.width : (grid.width - 3 * grid.spacing) / 4
                            height: chipItem.gap ? 12 : 26
                            // 8, pas 3 : une pastille est un objet qu'on prend,
                            // pas un champ. Le capuchon dedans garde 3 — deux
                            // rayons égaux emboîtés se lisent comme un rectangle
                            // dans un rectangle.
                            radius: 8
                            color: chipItem.gap ? "transparent"
                                   : chipItem.lit ? Qt.alpha(Theme.live, 0.14)
                                   : (rowHit.containsMouse && !chipItem.fixed ? Theme.rail : Theme.sunk)
                            border.width: chipItem.gap ? 0 : 1
                            border.color: root.capturing === chipItem.modelData.id || chipItem.lit ? Theme.live : Theme.edgeSoft

                            Text {
                                id: label
                                visible: !chipItem.gap
                                anchors {
                                    left: parent.left; leftMargin: 9
                                    right: keyCap.left; rightMargin: 8
                                    verticalCenter: parent.verticalCenter
                                }
                                elide: Text.ElideRight
                                text: chipItem.modelData.label
                                color: chipItem.lit ? Theme.live : (chipItem.fixed ? Theme.inkFaint : Theme.ink)
                                font.family: Theme.ui
                                font.pixelSize: 12
                            }

                            Rectangle {
                                id: keyCap
                                visible: !chipItem.gap
                                anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                                width: Math.max(shown.implicitWidth + 12, 30)
                                height: 18
                                radius: Theme.radiusSmall
                                color: root.capturing === chipItem.modelData.id ? Qt.alpha(Theme.live, 0.18) : Theme.rail
                                border.width: 1
                                border.color: root.capturing === chipItem.modelData.id ? Theme.live : Theme.edge

                                // Une case par touche : celles qu'on sait dessiner
                                // le sont, les autres s'écrivent. Un `⇧` de police
                                // était fin et creux à côté des lettres ; tracé, il
                                // a le poids de ce qui l'entoure.
                                Row {
                                    id: shown
                                    anchors.centerIn: parent
                                    spacing: 3
                                    visible: chipItem.spec.length > 0 && root.capturing !== chipItem.modelData.id

                                    Repeater {
                                        model: chipItem.parts

                                        Item {
                                            id: part
                                            required property string modelData
                                            readonly property color ink: chipItem.fixed ? Theme.inkFaint : Theme.ink
                                            width: drawn.drawn ? drawn.width : written.implicitWidth
                                            height: 11

                                            KeyGlyph {
                                                id: drawn
                                                token: Keymap.symbols(part.modelData)
                                                ink: part.ink
                                                width: 11; height: 11
                                            }

                                            Text {
                                                id: written
                                                visible: !drawn.drawn
                                                anchors.centerIn: parent
                                                text: Keymap.symbols(part.modelData)
                                                color: part.ink
                                                font.family: Theme.mono
                                                font.pixelSize: 10
                                            }
                                        }
                                    }
                                }

                                Text {
                                    anchors.centerIn: parent
                                    visible: !shown.visible
                                    text: root.capturing === chipItem.modelData.id ? "press…" : "—"
                                    color: root.capturing === chipItem.modelData.id ? Theme.live : Theme.inkFaint
                                    font.family: Theme.mono
                                    font.pixelSize: 10
                                }
                            }

                            MouseArea {
                                id: rowHit
                                anchors.fill: parent
                                enabled: !chipItem.gap
                                hoverEnabled: !chipItem.gap
                                onEntered: root.previewSpec(chipItem.spec)
                                onExited: root.endPreview()
                                onClicked: {
                                    if (chipItem.fixed)
                                        return;
                                    root.clash = "";
                                    root.capturing = root.capturing === chipItem.modelData.id
                                                     ? "" : chipItem.modelData.id;
                                }
                            }
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
    // its caps and the actions that use it.
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
            const spec = mod.length > 0 ? mod : Keymap.comboFrom(event);
            root.pressed = "";          // une frappe remplace l'aperçu, elle ne s'y ajoute pas
            root.showSpec(spec, Shell.modifierSides);
            const parts = spec.length > 0 ? spec.split("+") : [];
            root.keysStruck = parts.concat(root.heldIn(event.modifiers, "").filter((token) => parts.indexOf(token) < 0));
            return;
        }

        const spec = Keymap.comboFrom(event);
        if (spec.length === 0)
            return;

        root.clash = Keymap.holder(spec, root.capturing);
        // A key the system owns cannot be taken: the menu bar answers it before
        // the window ever sees it, so binding to it would do nothing at all.
        // Tab is the exception scope buys — it belongs to the code pane, so an
        // action of another pane may have it without either losing anything.
        for (const one of Keymap.reserved) {
            if (one.key === spec
                && !Keymap.sharable(Keymap.scopeOf(root.capturing), Keymap.scopeOf(one.id))) {
                root.capturing = "";
                return;
            }
        }
        Keymap.bind(root.capturing, spec);
        root.capturing = "";
    }

    Keys.onReleased: (event) => {
        event.accepted = true;
        if (!event.isAutoRepeat)
            root.keysStruck = root.heldIn(event.modifiers, root.modifierToken(event.key));
    }

    onVisibleChanged: {
        if (visible) {
            forceActiveFocus();
        } else {
            stopCapturing();
            hot = [];
            struck = "";
            keysStruck = [];
            sidesAt = 0;
        }
    }
}
