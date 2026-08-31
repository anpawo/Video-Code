// The arrangements the dock can be in, and nothing else.
//
// A template is a whole arrangement with a name, because the shape you want
// depends on what you are DOING: talking to the agent wants the conversation to
// own a column, cutting wants the timeline wide, writing wants the buffer beside
// the picture.
//
// It lives apart from Main.qml because it is DATA — a key in, a tree out, no
// state to read and nothing to break. That is also what makes a new arrangement
// a change to one file: add it to `templates`, add its branch to `tree()`, and
// the menu bar, the ⌘-number shortcuts and the persistence all pick it up.
pragma Singleton

import QtQuick

QtObject {
    id: root

    // The keys never change — a saved layout names them — but what they are
    // CALLED is what a person picks from a menu, so the labels say what you are
    // about to do rather than which panel is biggest.
    //
    // THE ORDER IS THE SHORTCUT. ⌘1…⌘4 are handed out down this list, and the
    // menu reads in the same order, so the first line is both the one you reach
    // for without looking and the one a first launch opens in. Video Coding
    // leads because a scene is written before it is cut.
    readonly property var templates: [
        { key: "code", label: "Video Coding" },
        { key: "edit", label: "Normal Editing" },
        { key: "agent", label: "Vibe Editing" },
        { key: "preview", label: "Preview" }
    ]

    function label(key) {
        for (let i = 0; i < root.templates.length; i++)
            if (root.templates[i].key === key)
                return root.templates[i].label;
        if (key.indexOf("user:") === 0)
            return key.substring(5);
        return key;
    }

    // The bin opens with pictures: a bin is something you recognise before you
    // read it, which is the whole reason a browser has thumbnails at all.
    //
    // Video Coding is the exception — there the bin shares the short pane at the
    // bottom right, cards need height and there is none — so that one opens as a
    // list. Either way it is per arrangement, and ⋯ → Display changes it.
    function options(key) {
        return { mediaDisplay: key === "code" ? "list" : "grid" };
    }

    function tree(key) {
        // Ids are prefixed per template so two arrangements never argue over the
        // same name in the registry while one is replacing the other.
        if (key === "agent")
            // The picture over the timeline, and everything you TALK to or TYPE
            // in stacked in one column on the right: the conversation, the code
            // it answers with, and the bin you name files from while asking. One
            // pane, three tabs — they are all "the thing I am telling it about",
            // and none of them is worth a column of its own while the other two
            // are idle.
            //
            // Everything but the picture is stacked in one column on the right:
            // the conversation first, then the code it answers with, the bin you
            // name files from, and the timeline. Vibe editing is asking for a
            // change and watching it land — the picture is what you watch, and
            // the rest are four ways of saying what you want, one at a time.
            return {
                t: "x", id: "a-root", dir: "h", size: 1, nodes: [
                    { t: "s", id: "a-stage", keys: ["preview"], current: 0, size: 0.63 },
                    { t: "s", id: "a-chat", keys: ["agent", "code", "media", "timeline"], current: 0, size: 0.37 }
                ]
            };

        if (key === "code")
            // Writing the scene by hand, and this is the arrangement it is
            // written in. The buffer takes the left of the top row — code is
            // read down a column, and a pane that stops halfway turns every
            // function into a scroll — with the agent stacked behind it as a
            // tab, because what the agent answers with IS the code.
            //
            // The picture takes the rest of that row, and the timeline runs the
            // WHOLE width underneath, with the bin as a tab behind it: time is
            // the one thing here whose meaning is horizontal, and a bin sharing
            // that row would take from the only pane that needs the width.
            return {
                t: "x", id: "c-root", dir: "v", size: 1, nodes: [
                    {
                        // Not invented: the proportions this arrangement was
                        // dragged to in use, and then kept.
                        t: "x", id: "c-top", dir: "h", size: 0.63, nodes: [
                            { t: "s", id: "c-code", keys: ["code", "agent"], current: 0, size: 0.456 },
                            { t: "s", id: "c-stage", keys: ["preview"], current: 0, size: 0.544 }
                        ]
                    },
                    { t: "s", id: "c-time", keys: ["timeline", "media"], current: 0, size: 0.37 }
                ]
            };

        if (key === "preview")
            // Watching, not editing. The picture gets everything the window can
            // give it and the timeline keeps only what a playhead needs to be
            // scrubbed; the bin, the buffer and the conversation are closed
            // rather than shrunk, because a pane too small to use is worse than
            // one that is not there.
            return {
                t: "x", id: "p-root", dir: "v", size: 1, nodes: [
                    { t: "s", id: "p-stage", keys: ["preview"], current: 0, size: 0.82 },
                    { t: "s", id: "p-time", keys: ["timeline"], current: 0, size: 0.18 }
                ]
            };

        // Edit: the everyday one, and the one with NO code in it.
        //
        // Cutting is not writing. The files run down the left where you pick
        // from them, the picture takes the rest of the top, and the timeline
        // runs the FULL width along the bottom the way every NLE lays out —
        // because it is the one pane whose meaning is horizontal, and time cut
        // short on the left is time you have to scroll to.
        //
        // The buffer is not here at all: this arrangement is for the half of
        // the work where the scene is already written. It is one tick away in
        // View → Docks, and Video Coding is the arrangement built around it.
        // The agent stands behind the files, where it costs nothing until it is
        // asked something.
        return {
            t: "x", id: "e-root", dir: "v", size: 1, nodes: [
                {
                    t: "x", id: "e-top", dir: "h", size: 0.63, nodes: [
                        { t: "s", id: "e-media", keys: ["media", "agent"], current: 0, size: 0.22 },
                        { t: "s", id: "e-stage", keys: ["preview"], current: 0, size: 0.78 }
                    ]
                },
                { t: "s", id: "e-time", keys: ["timeline"], current: 0, size: 0.37 }
            ]
        };
    }
}
