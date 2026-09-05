// Which key does what — as data the editor reads, not as a list that describes
// it from a distance.
//
// The point of keeping this apart is that the keyboard viewer and the code pane
// must never be able to disagree. The pane asks `Keymap.matches(event, "rename")`
// and the viewer draws `Keymap.combo("rename")`; rebinding writes one string and
// both change together. A shortcut list that is maintained by hand beside the
// handlers is a list that is wrong within a month.
//
// A combination is written the way a person says it: "Shift+F12", "Cmd+Left".
// The Qt modifier flags are an implementation detail and live only in `flagFor`.
pragma Singleton

import QtQuick

QtObject {
    id: root

    // What can be rebound, and where it applies. `where` is the group the
    // viewer draws them under.
    readonly property var actions: [
        { id: "definition",  label: "Go to definition",   where: "Code" },
        { id: "references",  label: "Find every use",     where: "Code" },
        { id: "rename",      label: "Rename everywhere",  where: "Code" },
        { id: "back",        label: "Back",               where: "Code" },
        { id: "forward",     label: "Forward",            where: "Code" },
        { id: "complete",    label: "Ask for completions", where: "Code" },
        { id: "save",        label: "Save the buffer",    where: "Code" },

        { id: "execute",     label: "Execute the scene",  where: "Scene" },
        // In the Code group, and deliberately: the caret is what it plays
        // from, so it has to work with your hands in the pane.
        { id: "playFromCaret", label: "Play from this line", where: "Code" },

        // `only` is the qualifier the board prints beside the key. All five are
        // keys a text editor already owns, so they belong to whichever of the
        // two has the caret — and a board that did not say so would be claiming
        // Space plays while you are writing a scene, which it does not.
        { id: "play",        label: "Play / pause",       where: "Transport", only: "outside the code pane" },
        { id: "toStart",     label: "Go to the start",    where: "Transport", only: "outside the code pane" },
        { id: "toEnd",       label: "Go to the end",      where: "Transport", only: "outside the code pane" },
        { id: "prevFrame",   label: "Previous frame",     where: "Transport", only: "outside the code pane" },
        { id: "nextFrame",   label: "Next frame",         where: "Transport", only: "outside the code pane" },
        // The moments the scene named with `timestamp()`. The frame keys with
        // Shift held: the same direction, a bigger step.
        { id: "prevMarker",  label: "Previous marker",    where: "Transport", only: "outside the code pane" },
        { id: "nextMarker",  label: "Next marker",        where: "Transport", only: "outside the code pane" },

        // The range. Two keys every editor on this machine already spells the
        // same way, and one to give the whole scene back.
        { id: "markIn",      label: "Mark in",            where: "Transport", only: "outside the code pane" },
        { id: "markOut",     label: "Mark out",           where: "Transport", only: "outside the code pane" },
        { id: "clearMarks",  label: "Clear the range",    where: "Transport", only: "outside the code pane" }
    ]

    // What the system owns. Listed so the board is honest about which keys are
    // taken, but not rebindable here: these are native menu shortcuts, and Qt
    // hands them to macOS rather than to the window.
    readonly property var reserved: [
        { id: "layout",    label: "Switch arrangement", key: "Cmd+1…4" },
        { id: "settings",  label: "Settings",           key: "Cmd+," },
        { id: "shortcuts", label: "This board",         key: "Cmd+/" },
        { id: "indent",    label: "Four spaces",        key: "Tab" },
        { id: "dismiss",   label: "Dismiss",            key: "Esc" }
    ]

    // The bindings themselves. Replaced wholesale rather than mutated, because a
    // QML binding does not hear a key being written into a `var` map.
    property var bindings: ({
        "definition": "F12",
        "references": "Shift+F12",
        "rename":     "F2",
        "back":       "Cmd+←",
        "forward":    "Cmd+→",
        "complete":   "Ctrl+Space",
        "save":       "Cmd+S",
        "execute":    "Cmd+R",
        "playFromCaret": "Cmd+Enter",
        "play":       "Space",
        "toStart":    "↓",
        "toEnd":      "↑",
        "prevFrame":  "←",
        "nextFrame":  "→",
        "prevMarker": "Shift+←",
        "nextMarker": "Shift+→",
        "markIn":     "I",
        "markOut":    "O",
        "clearMarks": "Shift+X"
    })

    // Raised when a binding changes, so the shell can persist the whole map.
    signal changed()

    // The same binding, spelled the way a QML `Shortcut` wants it.
    //
    // Two vocabularies meet here: this file says what a person presses (`Cmd`,
    // `←`), and Qt's portable sequence says `Ctrl` for ⌘ and `Left` for ←. The
    // translation lives in one function so a rebinding reaches the shortcuts as
    // well as the code pane — without it, half the keyboard board would be a
    // list of things the shell does not actually obey.
    function sequence(id) {
        const spec = root.combo(id);
        if (spec.length === 0)
            return "";

        const names = ({ "←": "Left", "→": "Right", "↑": "Up", "↓": "Down" });
        let parts = [];
        for (const mod of root.modsOf(spec))
            parts.push(mod === "Cmd" ? "Ctrl" : (mod === "Ctrl" ? "Meta" : mod));

        const base = root.baseOf(spec);
        parts.push(names[base] !== undefined ? names[base] : base);
        return parts.join("+");
    }

    function combo(id) {
        return root.bindings[id] !== undefined ? root.bindings[id] : "";
    }

    function modsOf(spec) {
        return spec.indexOf("+") >= 0 ? spec.slice(0, spec.lastIndexOf("+")).split("+") : [];
    }

    function baseOf(spec) {
        return spec.indexOf("+") >= 0 ? spec.slice(spec.lastIndexOf("+") + 1) : spec;
    }

    // ── macOS swaps ⌘ and ⌃ ───────────────────────────────────────────────
    // Qt reports the Command key as ControlModifier and the Control key as
    // MetaModifier, so that a shortcut written once lands on the key a Mac user
    // expects. Everything above this line says "Cmd" and means the ⌘ key; this
    // is the only place that knows what Qt calls it.
    function flagFor(name) {
        if (name === "Cmd")   return Qt.ControlModifier;
        if (name === "Ctrl")  return Qt.MetaModifier;
        if (name === "Shift") return Qt.ShiftModifier;
        if (name === "Alt")   return Qt.AltModifier;
        return 0;
    }

    // The keys a combination can end on, by the name the board prints on them.
    readonly property var codes: ({
        "←": Qt.Key_Left, "→": Qt.Key_Right, "↑": Qt.Key_Up, "↓": Qt.Key_Down,
        "Space": Qt.Key_Space, "Enter": Qt.Key_Return, "Backspace": Qt.Key_Backspace,
        "Tab": Qt.Key_Tab, "Esc": Qt.Key_Escape, "Home": Qt.Key_Home, "End": Qt.Key_End,
        "F1": Qt.Key_F1, "F2": Qt.Key_F2, "F3": Qt.Key_F3, "F4": Qt.Key_F4,
        "F5": Qt.Key_F5, "F6": Qt.Key_F6, "F7": Qt.Key_F7, "F8": Qt.Key_F8,
        "F9": Qt.Key_F9, "F10": Qt.Key_F10, "F11": Qt.Key_F11, "F12": Qt.Key_F12,
        "-": Qt.Key_Minus, "=": Qt.Key_Equal, "[": Qt.Key_BracketLeft,
        "]": Qt.Key_BracketRight, ";": Qt.Key_Semicolon, "'": Qt.Key_Apostrophe,
        ",": Qt.Key_Comma, ".": Qt.Key_Period, "/": Qt.Key_Slash, "\\": Qt.Key_Backslash,
        "`": Qt.Key_QuoteLeft
    })

    function codeFor(name) {
        if (root.codes[name] !== undefined)
            return root.codes[name];
        // Letters and digits are their own code: Qt.Key_A is 'A', Qt.Key_0 is '0'.
        return name.length === 1 ? name.toUpperCase().charCodeAt(0) : 0;
    }

    // Does this key event fire this action? Modifiers must match EXACTLY —
    // otherwise ⌘← would also answer to ⇧⌘←, which is a selection gesture.
    function matches(event, id) {
        const spec = root.combo(id);
        if (spec.length === 0)
            return false;

        const base = root.codeFor(root.baseOf(spec));
        if (base === 0 || event.key !== base)
            return false;

        let wanted = 0;
        for (const name of root.modsOf(spec))
            wanted |= root.flagFor(name);

        const held = event.modifiers & (Qt.ControlModifier | Qt.MetaModifier | Qt.ShiftModifier | Qt.AltModifier);
        return held === wanted;
    }

    // A real keypress, written the way this file writes combinations. Null when
    // the key pressed was only a modifier: a modifier alone is not a shortcut.
    function comboFrom(event) {
        if (event.key === Qt.Key_Control || event.key === Qt.Key_Meta
            || event.key === Qt.Key_Shift || event.key === Qt.Key_Alt)
            return "";

        let base = "";
        for (const name in root.codes)
            if (root.codes[name] === event.key)
                base = name;
        if (base.length === 0 && event.key >= 0x20 && event.key < 0x7f)
            base = String.fromCharCode(event.key).toUpperCase();
        if (base.length === 0)
            return "";

        let parts = [];
        if (event.modifiers & Qt.ControlModifier) parts.push("Cmd");
        if (event.modifiers & Qt.MetaModifier)    parts.push("Ctrl");
        if (event.modifiers & Qt.AltModifier)     parts.push("Alt");
        if (event.modifiers & Qt.ShiftModifier)   parts.push("Shift");
        parts.push(base);
        return parts.join("+");
    }

    // Who else already holds this combination — the question that has to be
    // answered BEFORE a rebinding lands, not after two things start firing.
    function holder(spec, exceptId) {
        for (const action of root.actions)
            if (action.id !== exceptId && root.combo(action.id) === spec)
                return action.label;
        for (const one of root.reserved)
            if (one.key === spec)
                return one.label;
        return "";
    }

    function bind(id, spec) {
        let next = ({});
        for (const key in root.bindings)
            next[key] = root.bindings[key];
        // Whoever held it loses it: two actions on one combination means one of
        // them silently never fires.
        for (const key in next)
            if (key !== id && next[key] === spec)
                next[key] = "";
        next[id] = spec;
        root.bindings = next;
        root.changed();
    }

    function restore(saved) {
        if (!saved)
            return;
        let next = ({});
        for (const key in root.bindings)
            next[key] = saved[key] !== undefined ? saved[key] : root.bindings[key];
        root.bindings = next;
    }
}
