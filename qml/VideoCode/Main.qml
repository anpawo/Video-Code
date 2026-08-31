// The editor shell.
//
// One dock, described by a TREE: a node is either a slot holding tabs or a split
// holding more nodes. There are no named layouts — two fixed arrangements to
// choose between answered a question nobody asked ("which of my two moods is
// this?") while refusing the one they did ("put the code where I want it").
//
// Every gesture is one edit to that tree:
//   · drop a tab on a slot's strip or middle  → the slot gains a tab
//   · drop it near a slot's edge              → the slot becomes a split of two
//   · drop it outside the window              → it leaves in a window of its own
//   · close the last tab of a slot            → the slot is pruned away
// The tree is then written to disk, so the arrangement outlives the process.
//
// All shared state lives here and the panels are views onto it, so moving a
// panel cannot lose your selection, your playhead or your unsaved buffer: the
// items themselves are created once, below, and only ever change parent.
pragma ComponentBehavior: Bound

import QtQml
import QtQuick
import QtQuick.Controls
import QtQuick.Window

ApplicationWindow {
    id: app

    // An editor opens filling the screen: every pane in this dock is sized as a
    // fraction of the window, so a small window makes all six of them useless at
    // once. The width/height below are only what a restored window falls back to.
    width: 1440
    height: 900
    // Shown maximized, or not shown at all.
    //
    // Said with `visibility` alone: setting `visible` beside it is a conflict Qt
    // warns about and resolves in an order nobody should have to know — and here
    // the losing side would be a window appearing when it was asked not to.
    //
    // It is asked not to because macOS has no public way to choose which Space a
    // window opens on (only private CoreGraphics calls), so a window opened by a
    // check lands on whatever desktop its author happens to be working on. The
    // fix is not to place it better. It is to not open one.
    visibility: Shell.headless ? ApplicationWindow.Hidden : ApplicationWindow.Maximized
    // The window is named after the arrangement you are in, not after the
    // program: which of them you are looking at is the one thing a title bar can
    // tell you that the window itself does not already show.
    title: templateLabel(template)
    color: Theme.ground

    // ── Shared state ──────────────────────────────────────────────────────
    // Nothing, until the buffer has been executed. There used to be a stand-in
    // scene here — five invented clips with names like `interview.mp4` — and it
    // was the right thing while the chrome was being built against no model at
    // all. It is the wrong thing now: the timeline is a picture OF THE CODE, and
    // a picture of something else is worse than no picture, because it is read
    // as an answer. The empty state says what to press instead.
    readonly property var emptyScene: ({ duration: 0, elements: [], waits: [] })

    property int selectedIndex: -1
    property real playhead: 0
    property bool playing: false

    // ── What a gesture snaps to ───────────────────────────────────────────
    // The moments a drop or a trim should prefer over the arithmetic mean of
    // wherever your hand stopped: where clips start and end, where the scene
    // waits, where the playhead is, where the range is marked.
    //
    // Tenths are the fallback, not the rule. Snapping only to a grid makes an
    // editor that cannot line two things up exactly — which is the one thing
    // you use the timeline for.
    readonly property var snapPoints: {
        const out = [0];
        for (const one of shownScene.elements) {
            out.push(one.l);
            out.push(one.l + one.d);
        }
        for (const gap of (shownScene.waits !== undefined ? shownScene.waits : [])) {
            out.push(gap.at);
            out.push(gap.at + gap.d);
        }
        out.push(playhead);
        if (markIn >= 0) out.push(markIn);
        if (markOut >= 0) out.push(markOut);
        return out;
    }

    // `exact` is ⌘ held: no snapping at all, the moment under the pointer.
    function snapTime(seconds, exact) {
        if (exact)
            return Math.round(seconds * 100) / 100;

        // Eight pixels' worth of forgiveness, in seconds — the same distance on
        // screen whatever the zoom, which is what makes it feel like the same
        // magnet at every scale.
        const reach = 8 / Math.max(timeline.pxPerSecond, 1);
        let best = -1;
        let near = reach;
        for (const one of snapPoints) {
            const d = Math.abs(one - seconds);
            if (d < near) {
                near = d;
                best = one;
            }
        }
        if (best >= 0)
            return Math.round(best * 100) / 100;
        return Math.round(seconds * 10) / 10;
    }

    // ── The range ─────────────────────────────────────────────────────────
    // Two moments, in seconds, or -1 for "not set". They are a VIEW of the
    // scene, not part of it: nothing in the code says which part of a scene you
    // are working on this afternoon, and writing it there would be writing a
    // preference into a program.
    //
    // What they change is what Space means. Play with a range set plays the
    // range and stops at its end — the loop you cut against — and everything
    // outside it is dimmed on the timeline so you can see what you are ignoring.
    property real markIn: -1
    property real markOut: -1

    readonly property bool ranged: markIn >= 0 && markOut > markIn

    function setMarkIn() {
        markIn = playhead;
        // An out point before the in point is not a range, it is a mistake with
        // a number in it. The one you just placed is the one that stands.
        if (markOut >= 0 && markOut <= markIn)
            markOut = -1;
        source.say("in at " + playhead.toFixed(2) + "s");
    }

    function setMarkOut() {
        markOut = playhead;
        if (markIn >= 0 && markIn >= markOut)
            markIn = -1;
        source.say("out at " + playhead.toFixed(2) + "s");
    }

    function clearMarks() {
        markIn = -1;
        markOut = -1;
        source.say("the whole scene again");
    }

    readonly property var selectedElement:
        selectedIndex >= 0 && selectedIndex < shownScene.elements.length
        ? shownScene.elements[selectedIndex]
        : null

    // ── The dock ──────────────────────────────────────────────────────────
    // Panels are created once, below, and never move house: a slot is told which
    // keys it holds and reparents those items into itself. Everything about the
    // arrangement is therefore this tree, and a gesture is one edit to it.
    readonly property var panelItems: ({
        "media": media,
        "library": library,
        "preview": preview,
        "timeline": timeline,
        "agent": agent,
        "code": source
    })

    // The code tab carries the file it is showing, and only while it is the tab
    // you are looking at: a slot that holds Code behind Agent has no room to
    // spell out a filename for a pane nobody can see, and the name would then be
    // stale advice rather than a label. The dot is the unsaved mark — until now
    // the pane knew it was modified and had nowhere to say so.
    readonly property var panelTitles: ({
        "media": "Media",
        "library": "Library",
        "preview": "Preview",
        "timeline": "Timeline",
        "agent": "Agent",
        "code": "Code"
    })

    // Whether the Code pane is the CURRENT tab of whichever slot holds it.
    property bool codeShown: false

    function currentKeys(node, out) {
        if (node.t === "s") {
            if (node.keys.length > 0)
                out.push(node.keys[Math.max(0, Math.min(node.current, node.keys.length - 1))]);
            return out;
        }
        for (const child of (node.nodes || []))
            currentKeys(child, out);
        return out;
    }

    function refreshCodeShown() {
        let shown = currentKeys(tree, []);
        for (const one of floats)
            if (one.keys.length > 0)
                shown.push(one.keys[Math.max(0, Math.min(one.current, one.keys.length - 1))]);
        codeShown = shown.indexOf("code") >= 0;
    }

    readonly property var panelKeys: ["media", "library", "preview", "timeline", "agent", "code"]

    property var tree: defaultTree()

    // Panels that live in a window of their own: {id, keys, current, x, y, w, h}.
    property var floats: []

    // Set while a tab is in flight, so the slot under the cursor can show where
    // it would land.
    property string hoverSlot: ""
    property string hoverZone: ""

    // id → the Item drawing that node, filled by the tree as it renders. It is
    // what turns a cursor position into "which slot is that", and what lets the
    // saved layout record the sizes the user dragged the handles to.

    property int nextId: 1

    function makeId() {
        return "n" + (nextId++);
    }

    // ── Measuring the arrangement ─────────────────────────────────────────
    // Two readings of the same number, for the two moments you want it.
    //
    // `measuring` blanks every pane and writes the share of the window it takes:
    // the panes stop being what they contain and become what they measure, which
    // is the only way to compare them at a glance. It lasts until the next click,
    // because it is a question, not a mode you work in.
    //
    // `tip` is the same figure during a drag, next to the pointer, for the panes
    // the drag is moving. Deciding a size while it is still under your hand beats
    // dragging, letting go, looking, and dragging again.
    property bool measuring: false
    property var tip: null

    // The area the panes divide between them, handed to every slot so a share is
    // a share of the same thing wherever it is read.
    readonly property Item dockArea: dockArea

    // A tenth of a percent, with a comma — the same reading the panes give, so a
    // splitter and the pane it moves never disagree about what they measure.
    function sharePercent(part, whole) {
        return whole > 0 ? (part / whole * 100).toFixed(1).replace(".", ",") + "%" : "—";
    }

    function showTip(x, y, text) { tip = { x: x, y: y, text: text }; }
    function hideTip() { tip = null; }

    // The arrangement a first launch opens in. Video Coding, because this is an
    // application for writing videos in Python before it is anything else, and
    // the window ought to open on the thing you came to do.
    property string template: "code"

    // How the bin draws itself: "grid" or "list". It belongs to the arrangement
    // rather than to the application, because it answers the same question the
    // arrangement does — what are you doing right now. Writing the scene by hand
    // wants filenames in a column; cutting wants pictures.
    property string mediaDisplay: "grid"

    // Media the user has added this session. The scene's own assets come from
    // the compiled buffer and are not ours to edit; these sit beside them until
    // the day adding a file writes an input into the source, which is the same
    // door a timeline drag will use.
    property var addedAssets: []

    function kindOfFile(path) {
        const extension = path.split(".").pop().toLowerCase();
        if (["mp4", "mov", "mkv", "webm", "avi"].indexOf(extension) >= 0)
            return "video";
        if (["wav", "mp3", "aac", "flac", "m4a", "ogg"].indexOf(extension) >= 0)
            return "sound";
        if (["png", "jpg", "jpeg", "svg", "gif", "webp"].indexOf(extension) >= 0)
            return "image";
        return "";
    }

    function addMedia() {
        const chosen = Shell.pickMedia();
        if (!chosen || chosen.length === 0)
            return;

        const next = addedAssets.slice();
        for (let i = 0; i < chosen.length; i++) {
            const kind = kindOfFile(chosen[i]);
            // A file the engine has no input class for is not quietly filed
            // under a hue that would lie about what it is.
            if (kind === "")
                continue;
            next.push({ n: chosen[i].split("/").pop(), kind: kind, path: chosen[i] });
        }
        addedAssets = next;
    }

    // Trees the user has bent out of shape, keyed by template.
    property var layouts: ({})

    // Built-in arrangements the user has REPLACED, keyed by template. Where
    // `layouts` remembers a bend that Reset UI throws away, this is the new
    // shape itself — what Reset UI goes back TO.
    property var defaults: ({})

    // Arrangements the user has named and kept: [{ name, tree, floats, options }].
    // The three built-in templates are shapes to start from; these are the ones
    // that turned out to be worth keeping, and they sit in the same menus, under
    // keys of the form "user:<name>".
    property var saved: []

    function savedIndex(name) {
        for (let i = 0; i < saved.length; i++)
            if (saved[i].name === name)
                return i;
        return -1;
    }

    // A built-in arrangement, replaced by yours.
    //
    // Save display… under the name of one of the four — "Video Coding", say —
    // and it is that arrangement you are rewriting, not a fifth one beside it
    // with a confusing name. It holds for good: Reset UI then puts back YOUR
    // Video Coding, because the one it ships with stopped being the answer the
    // moment you said otherwise.
    function templateKeyNamed(name) {
        const wanted = name.trim().toLowerCase();
        for (const one of Layouts.templates)
            if (one.label.toLowerCase() === wanted)
                return one.key;
        return "";
    }

    // Saving over a name replaces it: two displays called the same thing is a
    // list you cannot read.
    function saveDisplay(name) {
        const snapshot = copy(tree);

        const builtIn = templateKeyNamed(name);
        if (builtIn.length > 0) {
            const nextDefaults = copy(defaults);
            nextDefaults[builtIn] = {
                tree: snapshot,
                floats: copy(floats),
                options: { mediaDisplay: mediaDisplay }
            };
            defaults = nextDefaults;

            // The template's own edits are dropped: they were bends of the old
            // shape, and the shape has changed.
            const trimmed = copy(layouts);
            delete trimmed[builtIn];
            layouts = trimmed;

            template = builtIn;
            saveLayout();
            Shell.setDockTemplates(menuTemplates());
            return;
        }

        const entry = {
            name: name,
            tree: snapshot,
            floats: copy(floats),
            options: { mediaDisplay: mediaDisplay }
        };

        const next = copy(saved);
        const at = savedIndex(name);
        if (at >= 0)
            next[at] = entry;
        else
            next.push(entry);

        saved = next;
        template = "user:" + name;
        saveLayout();
        Shell.setDockTemplates(menuTemplates());
        Shell.setDockDisplays(menuDisplays());
    }

    // Keep what is on screen as what this display IS.
    //
    // Save display… already does it — type the name of the arrangement you are
    // in and it rewrites that one rather than making a fifth with a confusing
    // name — but that asks you to know the rule and to type the name exactly.
    // This is the same act with the name filled in: whatever you are in, built-in
    // or your own, is now shaped like this, and Reset UI puts back THIS.
    function updateDefault() {
        if (template.length === 0)
            return;

        // Through `app`, not by bare name: the Save display… dialog is `id:
        // saveDisplay`, and an id wins over a function of the same name.
        if (template.indexOf("user:") === 0)
            app.saveDisplay(template.substring(5));
        else
            app.saveDisplay(templateLabel(template));

        source.say("updated " + templateLabel(template));
    }

    function loadDisplay(name) {
        const at = savedIndex(name);
        if (at < 0)
            return;

        // What you are leaving is kept the way switching template keeps it, so
        // loading a display never costs you the one you were in.
        const kept = copy(layouts);
        const snapshot = copy(tree);
        kept[template] = { tree: snapshot, floats: copy(floats), options: { mediaDisplay: mediaDisplay } };
        layouts = kept;

        const entry = saved[at];
        restoring = true;
        template = "user:" + name;
        tree = copy(entry.tree);
        floats = copy(entry.floats || []);
        mediaDisplay = entry.options && entry.options.mediaDisplay === "list" ? "list" : "grid";
        restoring = false;

        saveLayout();
        Shell.setDockTemplates(menuTemplates());
    }

    // The bin opens as a details list where its pane is short — sharing a row
    // with the timeline leaves no height for thumbnails, and a squashed picture
    // of a file is worth less than its name. Everywhere else it opens as a grid.
    function templateLabel(key) { return Layouts.label(key); }
    function buildOptions(key) {
        const mine = defaults[key];
        return mine && mine.options ? copy(mine.options) : Layouts.options(key);
    }
    function buildTemplate(key) {
        // Yours if you have saved one under that name, otherwise the one it
        // ships with.
        const mine = defaults[key];
        return mine && mine.tree ? copy(mine.tree) : Layouts.tree(key);
    }

    function buildFloats(key) {
        const mine = defaults[key];
        return mine && mine.floats ? copy(mine.floats) : [];
    }

    function defaultTree() {
        return buildTemplate(template);
    }

    // Switching keeps what you did to the template you are leaving, floating
    // panels included: they belong to an arrangement as much as the panes do.
    function useTemplate(key) {
        if (key === template)
            return;

        if (key.indexOf("user:") === 0) {
            loadDisplay(key.substring(5));
            return;
        }

        const kept = copy(layouts);
        const snapshot = copy(tree);
        kept[template] = {
            tree: snapshot,
            floats: copy(floats),
            options: { mediaDisplay: mediaDisplay }
        };

        const saved = kept[key];
        const options = saved && saved.options ? saved.options : buildOptions(key);
        layouts = kept;
        template = key;
        restoring = true;
        tree = saved && saved.tree ? saved.tree : buildTemplate(key);
        floats = saved && saved.floats ? saved.floats : buildFloats(key);
        mediaDisplay = options.mediaDisplay === "list" ? "list" : "grid";
        restoring = false;

        saveLayout();
        Shell.setDockTemplates(menuTemplates());
    }

    // The tree is replaced, never edited in place: a binding on `tree` does not
    // hear about a push() three levels down inside it.
    function copy(value) {
        return JSON.parse(JSON.stringify(value));
    }

    function eachNode(node, fn, parent, index) {
        fn(node, parent, index);
        if (node.t === "x")
            for (let i = 0; i < node.nodes.length; i++)
                eachNode(node.nodes[i], fn, node, i);
    }

    function findNode(root, id) {
        let found = null;
        eachNode(root, (node, parent, index) => {
            if (node.id === id)
                found = { node: node, parent: parent, index: index };
        });
        return found;
    }

    function slotOf(id) {
        const hit = findNode(tree, id);
        if (hit && hit.node.t === "s")
            return hit.node;
        for (let i = 0; i < floats.length; i++)
            if (floats[i].id === id)
                return floats[i];
        return null;
    }

    // Which panels are on screen at all — the rest are what the ⋯ menu offers to
    // bring back.
    function shownKeys() {
        const shown = [];
        eachNode(tree, (node) => {
            if (node.t === "s")
                for (let i = 0; i < node.keys.length; i++)
                    shown.push(node.keys[i]);
        });
        for (let i = 0; i < floats.length; i++)
            shown.push(...floats[i].keys);
        return shown;
    }

    // ── Editing the tree ──────────────────────────────────────────────────
    function pickTab(id, index) {
        const hit = findNode(tree, id);
        if (hit) {
            const next = copy(tree);
            // Read the panes as they STAND before replacing the tree.
            //
            // A dragged handle moves the items, not the model: the fractions in
            // the tree are still the ones it was rendered from. Every other edit
            // captures them first; picking a tab did not, so replacing the tree
            // re-rendered it from stale numbers and every pane you had resized
            // sprang back — which looked like switching tabs had a side effect.
            findNode(next, id).node.current = index;
            tree = next;
            saveLayout();
            return;
        }
        const nextFloats = copy(floats);
        for (let i = 0; i < nextFloats.length; i++)
            if (nextFloats[i].id === id)
                nextFloats[i].current = index;
        floats = nextFloats;
    }

    // An empty slot is not kept: a hole you cannot see is a hole you cannot fill
    // back in. What was closed comes back from the ⋯ menu, which is the list of
    // everything, not from a gap left in the dock.
    function prune(node) {
        // A gap is a node that draws nothing. It is kept for the same reason a
        // slot is: someone put it there on purpose.
        if (node.t === "g")
            return node.size > 0.02 ? node : null;

        if (node.t === "s")
            return node.keys.length > 0 ? node : null;

        const kept = [];
        for (let i = 0; i < node.nodes.length; i++) {
            const child = prune(node.nodes[i]);
            if (child)
                kept.push(child);
        }
        if (kept.length === 0)
            return null;

        // Space with nothing beside it is not space, it is a hole where a window
        // used to be — so a branch that has become all gaps goes with them.
        let onlyGaps = true;
        for (let i = 0; i < kept.length; i++)
            if (kept[i].t !== "g")
                onlyGaps = false;
        if (onlyGaps)
            return null;

        if (kept.length === 1) {
            // A split of one is not a split; it takes its parent's place and the
            // room that came with it.
            kept[0].size = node.size;
            return kept[0];
        }

        let total = 0;
        for (let i = 0; i < kept.length; i++)
            total += kept[i].size;
        for (let i = 0; i < kept.length; i++)
            kept[i].size = kept[i].size / total;

        node.nodes = kept;
        return node;
    }

    function settle(next) {
        const pruned = prune(next);
        // The dock is never nothing: an empty one is a slot waiting to be filled,
        // which is also the only thing you can drop a tab back onto.
        tree = pruned !== null
               ? pruned
               : { t: "s", id: makeId(), keys: [], current: 0, size: 1 };
    }

    function detach(next, nextFloats, key) {
        eachNode(next, (node) => {
            if (node.t !== "s")
                return;
            const at = node.keys.indexOf(key);
            if (at < 0)
                return;
            node.keys.splice(at, 1);
            node.current = Math.max(0, Math.min(node.current, node.keys.length - 1));
        });
        for (let i = 0; i < nextFloats.length; i++) {
            const at = nextFloats[i].keys.indexOf(key);
            if (at < 0)
                continue;
            nextFloats[i].keys.splice(at, 1);
            nextFloats[i].current = Math.max(0, Math.min(nextFloats[i].current, nextFloats[i].keys.length - 1));
        }
    }

    function dockTab(key, targetId, zone) {
        const next = copy(tree);
        const nextFloats = copy(floats).filter((one) => one.keys.length > 0 || one.keys.indexOf(key) >= 0);
        detach(next, nextFloats, key);

        // The dock's own edge: the arrangement that exists becomes one side of a
        // new split, and the tab becomes the other. Everything keeps its shape
        // and gives up a share of the window — which is what makes it read as
        // room being MADE rather than a pane being taken over.
        if (targetId === app.wholeDock) {
            const across = zone === "left" || zone === "right";
            const kept = prune(next);
            const leaf = { t: "s", id: makeId(), keys: [key], current: 0, size: 0.28 };
            if (kept === null) {
                leaf.size = 1;
                tree = leaf;
            } else {
                kept.size = 0.72;
                tree = {
                    t: "x", id: makeId(), dir: across ? "h" : "v", size: 1,
                    nodes: zone === "left" || zone === "top" ? [leaf, kept] : [kept, leaf]
                };
            }
            floats = nextFloats.filter((one) => one.keys.length > 0);
            return;
        }

        const hit = findNode(next, targetId);
        if (!hit) {
            // The slot it was aimed at is gone (it held only this tab). Put it
            // back where it came from rather than losing it.
            settle(next);
            floats = nextFloats.filter((one) => one.keys.length > 0);
            return;
        }

        if (zone === "center" || hit.node.t !== "s") {
            hit.node.keys.push(key);
            hit.node.current = hit.node.keys.length - 1;
        } else {
            const leaf = { t: "s", id: makeId(), keys: [key], current: 0, size: 0.5 };
            const kept = copy(hit.node);
            kept.size = 0.5;
            const split = {
                t: "x",
                id: makeId(),
                dir: zone === "left" || zone === "right" ? "h" : "v",
                size: hit.node.size,
                nodes: zone === "left" || zone === "top" ? [leaf, kept] : [kept, leaf]
            };
            if (hit.parent)
                hit.parent.nodes[hit.index] = split;
            else
                return settleRoot(split, nextFloats);
        }

        settle(next);
        floats = nextFloats.filter((one) => one.keys.length > 0);
    }

    function settleRoot(node, nextFloats) {
        settle(node);
        floats = nextFloats.filter((one) => one.keys.length > 0);
    }

    function closeTab(id, key) {
        const next = copy(tree);
        const nextFloats = copy(floats);
        detach(next, nextFloats, key);
        settle(next);
        floats = nextFloats.filter((one) => one.keys.length > 0);
        saveLayout();
    }

    // Bringing a panel back puts it where you last had the dock's attention —
    // the slot whose menu you opened — because that is the one you are looking at.
    function openPanel(key, whereId) {
        const target = slotOf(whereId) ? whereId : firstSlotId();
        // dockTab has already saved, and from the model: saving again here would
        // re-read panes that were replaced a moment ago and have no geometry yet.
        dockTab(key, target, "center");
    }

    function firstSlotId() {
        let first = "";
        eachNode(tree, (node) => {
            if (first === "" && node.t === "s")
                first = node.id;
        });
        return first;
    }

    // ── Space ─────────────────────────────────────────────────────────────
    // A SplitView shares out ALL of its room among its children, so a pane can
    // only ever shrink by growing a neighbour: there is no way to say "smaller,
    // and leave the rest empty". A gap is that neighbour — a node that takes a
    // share of the tree and draws nothing, so the window's own background shows
    // through and the splitter between them resizes the pane against the void.
    // True when the pane already has something on that side to give room to.
    // Where it has not, the dock offers a grip instead: an edge you can pull in
    // even though nothing is waiting to take the space.
    function hasNeighbour(id, side) {
        const hit = findNode(tree, id);
        if (!hit || !hit.parent)
            return false;
        if (hit.parent.dir !== (side === "left" || side === "right" ? "h" : "v"))
            return false;
        return side === "right" || side === "bottom"
               ? hit.index < hit.parent.nodes.length - 1
               : hit.index > 0;
    }

    // Pulling that grip. The first pixel of the drag builds the void the pane is
    // about to shrink into; every pixel after it just moves the boundary between
    // the two, which is the same arithmetic a splitter does.
    // Committed once, on release, never during the drag.
    //
    // Resizing rearranges the tree — a pane with nothing beside it has to be
    // wrapped in a split with a void — and rearranging destroys and rebuilds the
    // panes below that point, including the very grip under the pointer. Doing
    // it per pixel therefore cancelled the gesture on its first pixel. The drag
    // draws its own preview instead, and the model hears about it exactly once.
    function commitResize(slotId, side, deltaPixels) {
        if (Math.abs(deltaPixels) < 2)
            return;

        const horizontal = side === "left" || side === "right";
        const extent = app.paneExtent(slotId, horizontal);
        if (extent <= 0)
            return;
        const next = copy(tree);
        // Everything the user has dragged elsewhere, read while the panes still
        // stand as they are.
        let hit = findNode(next, slotId);
        if (!hit)
            return;

        const aligned = hit.parent && hit.parent.dir === (horizontal ? "h" : "v");
        // A whole share, in pixels: the pane's own length divided by the share it
        // holds — or, when it is about to become nearly all of a new split, the
        // pane's length itself.
        const total = aligned ? extent / Math.max(hit.node.size, 0.001) : extent;

        if (!aligned) {
            const gap = { t: "g", id: makeId(), size: 0.001 };
            const kept = copy(hit.node);
            kept.size = 0.999;
            const split = {
                t: "x",
                id: makeId(),
                dir: horizontal ? "h" : "v",
                size: hit.node.size,
                nodes: side === "left" || side === "top" ? [gap, kept] : [kept, gap]
            };
            if (hit.parent) {
                hit.parent.nodes[hit.index] = split;
                hit = findNode(next, slotId);
            } else {
                settle(split);
                commitResize(slotId, side, deltaPixels);
                return;
            }
        }

        const siblings = hit.parent.nodes;
        const after = side === "right" || side === "bottom";
        let neighbour = after ? hit.index + 1 : hit.index - 1;

        if (neighbour < 0 || neighbour >= siblings.length) {
            siblings.splice(after ? siblings.length : 0, 0,
                            { t: "g", id: makeId(), size: 0.001 });
            hit = findNode(next, slotId);
            neighbour = after ? hit.index + 1 : hit.index - 1;
        }

        const mine = siblings[hit.index];
        const theirs = siblings[neighbour];

        let delta = deltaPixels / total;
        if (!after)
            delta = -delta;
        delta = Math.max(-mine.size + 0.06, Math.min(delta, theirs.size - 0.001));

        mine.size += delta;
        theirs.size -= delta;

        settle(next);
        saveLayout();
    }

    // Where a pane is on the desktop, from the PLAN — the canvas computed it,
    // and asking an item would be asking the same question twice.
    function paneCentre(slotId) {
        const rect = dockArea.rectOf(slotId);
        if (!rect)
            return Qt.point(240, 240);
        return dockArea.mapToGlobal(rect.x + rect.w / 2, rect.y + rect.h / 2);
    }

    function paneExtent(slotId, horizontal) {
        const rect = dockArea.rectOf(slotId);
        if (!rect)
            return 0;
        return horizontal ? rect.w : rect.h;
    }

    // Moving a boundary. Written into the model on every move — the canvas keeps
    // its panes across a change, so there is no longer a grip that destroys
    // itself under the pointer. It used to be committed on release only, for
    // exactly that reason.
    function dragHandle(splitId, index, deltaPixels) {
        const rect = dockArea.splitRect(splitId);
        if (!rect || Math.abs(deltaPixels) < 0.4)
            return;

        const total = rect.dir === "h" ? rect.w : rect.h;
        if (total <= 0)
            return;

        const next = copy(tree);
        const hit = findNode(next, splitId);
        if (!hit || hit.node.t !== "x" || index + 1 >= hit.node.nodes.length)
            return;

        const mine = hit.node.nodes[index];
        const theirs = hit.node.nodes[index + 1];
        // Neither side below a usable width, and neither eating the other: a
        // pane you cannot see is a pane you cannot get back.
        const floor = (rect.dir === "h" ? 140 : 90) / total;
        let delta = deltaPixels / total;
        delta = Math.max(-mine.size + floor, Math.min(delta, theirs.size - floor));
        if (Math.abs(delta) < 0.0001)
            return;

        mine.size += delta;
        theirs.size -= delta;
        tree = next;
        saveLayout();
    }

    // What the two sides of a handle hold, as the figures shown while it moves.
    function shareAt(splitId, index) {
        const hit = findNode(tree, splitId);
        if (!hit || hit.node.t !== "x" || index + 1 >= hit.node.nodes.length)
            return "";
        return Math.round(hit.node.nodes[index].size * 100) + "%   "
             + Math.round(hit.node.nodes[index + 1].size * 100) + "%";
    }

    function hasSpaceBeside(slotId) {
        const hit = findNode(tree, slotId);
        if (!hit || !hit.parent)
            return false;
        for (let i = 0; i < hit.parent.nodes.length; i++)
            if (hit.parent.nodes[i].t === "g")
                return true;
        return false;
    }

    // ── Turning a cursor into a place ─────────────────────────────────────
    // Positions travel in GLOBAL coordinates: a drop may land in another window,
    // and a scene position means nothing over there. They are brought into the
    // canvas once, here, and compared against the PLAN — the rectangles the dock
    // laid the panes out with, rather than the items it laid out.
    function zoneIn(rect, lx, ly) {
        if (lx < rect.x || ly < rect.y || lx > rect.x + rect.w || ly > rect.y + rect.h)
            return "";

        const fx = (lx - rect.x) / rect.w;
        const fy = (ly - rect.y) / rect.h;

        // The shape of the zones is Qt's, because it is the one every docking
        // window on this machine has already taught: the middle two thirds in
        // both directions add a tab, and the ring around it splits — thirds left
        // and right, halves top and bottom of what is left.
        //
        //        +--------------+          +------------+
        //        |              |          |LLLL TT RRRR|
        //        |   CCCCCCCC   |   the    |LLLL TT RRRR|
        //        |   CCCCCCCC   |   ring:  |LLLL BB RRRR|
        //        |              |          |LLLL BB RRRR|
        //        +--------------+          +------------+
        if (fx > 1 / 6 && fx < 5 / 6 && fy > 1 / 6 && fy < 5 / 6)
            return "center";
        if (fx < 1 / 3)
            return "left";
        if (fx > 2 / 3)
            return "right";
        return fy < 0.5 ? "top" : "bottom";
    }

    // ── The dock's own edge ───────────────────────────────────────────────
    // A band along the outside of the whole dock, where a drop means "a new area
    // across the entire window" rather than "split the pane under the pointer".
    // Without it a tab could only ever divide the pane it landed on: to put the
    // timeline along the bottom of a window whose bottom is a corner of one
    // pane, there was nothing to aim at.
    readonly property real dockBand: 26

    // The name a drop uses for "not a pane — the dock itself". No slot can ever
    // be called this: ids are made by `makeId`.
    readonly property string wholeDock: "__dock__"

    function rootZoneAt(lx, ly) {
        if (lx < 0 || ly < 0 || lx > dockArea.width || ly > dockArea.height)
            return "";

        const band = Math.min(dockBand, Math.min(dockArea.width, dockArea.height) / 8);
        const edges = [
            { zone: "left", d: lx },
            { zone: "right", d: dockArea.width - lx },
            { zone: "top", d: ly },
            { zone: "bottom", d: dockArea.height - ly }
        ];
        let closest = edges[0];
        for (let i = 1; i < edges.length; i++)
            if (edges[i].d < closest.d)
                closest = edges[i];
        return closest.d < band ? closest.zone : "";
    }

    function resolve(x, y) {
        const at = dockArea.mapFromGlobal(x, y);
        // The committed arrangement, not the preview: resolving against the
        // preview made each answer move the panes that produced it, and the
        // layout throbbed under the held tab instead of following the mouse.
        const panes = dockArea.hitPlan.panes;

        // A tab strip wins over everything, the dock's own edge included: a
        // strip that happens to run along the top of the window is still a row
        // of tabs, and dropping on one has never meant anything else.
        for (const one of panes) {
            if (one.kind !== "s")
                continue;
            if (at.x >= one.x && at.x <= one.x + one.w
                && at.y >= one.y && at.y < one.y + 28)
                return { id: one.id, zone: "center" };
        }

        // Then the outside of the dock — a new area spanning the window.
        const outer = rootZoneAt(at.x, at.y);
        if (outer !== "")
            return { id: app.wholeDock, zone: outer };

        for (const one of panes) {
            if (one.kind !== "s")
                continue;
            const zone = zoneIn(one, at.x, at.y);
            if (zone !== "")
                return { id: one.id, zone: zone };
        }
        return null;
    }

    // ── The hole that opens before you let go ─────────────────────────────
    //
    // What OBS does, and what makes its dock read as a room rather than as a
    // diagram: while a panel is in the air the layout ITSELF opens a gap for it,
    // so the arrangement you are about to get is the one on screen — not a
    // coloured rectangle drawn over the one you have.
    //
    // Qt calls it `insertGap`: a placeholder goes into the layout at the drop
    // position and everything re-lays out around it. This is the same idea in
    // the dock's own terms — a node of kind "p" spliced into a COPY of the tree,
    // which the canvas draws instead of the real one until the drag ends.
    // Nothing is committed: let go outside and the copy is thrown away.
    property var previewTree: null

    // True from the first move of a tab drag until it lands. The dock's own edge
    // is drawn while it is true, and the panes only slide while it is true.
    property bool tabInFlight: false

    function holeNode(size) {
        return { t: "p", id: "__hole__", size: size };
    }

    function buildPreview(targetId, zone) {
        // A drop that only adds a tab moves nothing: the strip is where it lands
        // and the pane keeps every pixel it has. The slot draws that one itself.
        if (zone === "" || zone === "center")
            return null;

        const across = zone === "left" || zone === "right";
        const first = zone === "left" || zone === "top";

        if (targetId === app.wholeDock) {
            const kept = copy(tree);
            kept.size = 0.72;
            return {
                t: "x", id: "__holesplit__", dir: across ? "h" : "v", size: 1,
                nodes: first ? [holeNode(0.28), kept] : [kept, holeNode(0.28)]
            };
        }

        const next = copy(tree);
        const hit = findNode(next, targetId);
        if (!hit)
            return null;

        const kept = copy(hit.node);
        kept.size = 0.5;
        const split = {
            t: "x", id: "__holesplit__", dir: across ? "h" : "v", size: hit.node.size,
            nodes: first ? [holeNode(0.5), kept] : [kept, holeNode(0.5)]
        };
        if (!hit.parent)
            return split;
        hit.parent.nodes[hit.index] = split;
        return next;
    }

    function dragOver(fromId, x, y) {
        tabInFlight = true;
        const target = resolve(x, y);
        const id = target ? target.id : "";
        const zone = target ? target.zone : "";
        if (id === hoverSlot && zone === hoverZone)
            return;

        hoverSlot = id;
        hoverZone = zone;
        previewTree = buildPreview(id, zone);
    }

    function drop(fromId, key, x, y) {
        hoverSlot = "";
        hoverZone = "";
        tabInFlight = false;
        previewTree = null;

        const target = resolve(x, y);
        if (target) {
            // Dropping a lone tab back onto its own slot changes nothing, and
            // must not tear it out and put it back.
            const from = slotOf(fromId);
            if (!(target.id === fromId && (target.zone === "center" || (from && from.keys.length === 1))))
                dockTab(key, target.id, target.zone);
        } else {
            floatTab(key, x, y);
        }
    }

    // ── Floating ──────────────────────────────────────────────────────────
    // The pop-out button in a slot's strip: the tab on top leaves for a window
    // of its own, landing over the pane it came from.
    function floatCurrent(slotId) {
        const here = slotOf(slotId);
        if (!here || here.keys.length === 0)
            return;
        const at = app.paneCentre(slotId);
        floatTab(here.keys[here.current], at.x, at.y);
    }

    function floatTab(key, x, y) {
        const next = copy(tree);
        const nextFloats = copy(floats);
        detach(next, nextFloats, key);
        nextFloats.push({
            id: makeId(),
            keys: [key],
            current: 0,
            // Dropped where you let go, not centred on the screen: the window
            // appears under your hand.
            x: Math.round(x - 160),
            y: Math.round(y - 14),
            w: 520,
            h: 360
        });
        settle(next);
        floats = nextFloats.filter((one) => one.keys.length > 0);
        saveLayout();
    }

    // ── Persistence ───────────────────────────────────────────────────────
    // Sizes are no longer read back off the panes. The model IS the size: a
    // handle writes fractions into the tree as it moves, and the canvas lays
    // the panes out from them. What used to be `captureSizes` existed because
    // the two could disagree — and it was itself the source of the drift it
    // was written to prevent.

    property bool restoring: false

    // fromModel: the tree in hand is already the truth — do not go and read the
    // panes for their sizes. After a structural change the new panes have not
    // been laid out yet, and reading them then wrote a layout of three equal
    // columns over the one the user had.
    function saveLayout() {
        if (restoring || !restored)
            return;
        // Moving a pane is an ATTEMPT, not a decision.
        //
        // The arrangement you are bending lives in memory for as long as the
        // window does — switch away and back and your bend is still there — and
        // it is never written here. What the file holds is what you decided:
        // the shape pinned with Update default, the displays saved under a
        // name, your keys, your colours, and which arrangement you were in.
        //
        // Otherwise every drag quietly became the new normal: you could not try
        // a wider timeline for ten minutes without owning it, and Reset was the
        // only way back to a shape you never meant to leave.
        Shell.saveLayout(JSON.stringify({
            version: 3,
            template: template,
            defaults: defaults,
            saved: saved,
            codeTheme: Theme.codeTheme,
            codeThemePicked: codeThemePicked,
            keymap: Keymap.bindings
        }));
    }

    // What a restart forgets, and why it is not a bug.
    //
    // Where the panes ARE does not survive closing the app unless you said it
    // should: Update default pins the shape of an arrangement, Save display
    // keeps one under a name. Everything else — the pane you widened while
    // reading something, the tab you dragged across to compare two things — is
    // an attempt, and the window it was made in is as long as it lasts.

    // A layout read from disk is data from another run: it may name panels this
    // build no longer has, or have been written by a version that arranged them
    // differently. Anything unrecognised is dropped rather than trusted.
    function sanitise(node) {
        if (node.t === "g")
            return { t: "g", id: node.id, size: node.size > 0 ? node.size : 0.2 };

        if (node.t === "s") {
            node.keys = (node.keys || []).filter((key) => panelKeys.indexOf(key) >= 0);
            node.current = Math.max(0, Math.min(node.current || 0, node.keys.length - 1));
            return node.keys.length > 0 ? node : null;
        }
        if (node.t !== "x")
            return null;

        const kept = [];
        for (let i = 0; i < (node.nodes || []).length; i++) {
            const child = sanitise(node.nodes[i]);
            if (child)
                kept.push(child);
        }
        if (kept.length === 0)
            return null;

        let allGaps = true;
        for (let i = 0; i < kept.length; i++)
            if (kept[i].t !== "g")
                allGaps = false;
        if (allGaps)
            return null;

        if (kept.length === 1) {
            kept[0].size = node.size;
            return kept[0];
        }
        node.nodes = kept;
        return node;
    }

    // Ids read from a file must not collide with ids minted this run.
    function highestId(node) {
        let highest = 0;
        eachNode(node, (one) => {
            const number = parseInt(String(one.id).replace("n", ""), 10);
            if (!isNaN(number) && number > highest)
                highest = number;
        });
        return highest;
    }

    // Whether the file on disk has been read yet. NOTHING is written before it
    // has.
    //
    // A start that failed half-way — a bridge this binary does not have, a
    // scene that would not run — leaves the window on the shape it ships with
    // and the restore never reached. The first pane moved after that saved THAT
    // over the arrangement you had built, and the loss looked like the dock
    // forgetting rather than like a start that never finished. A save is only
    // ever an edit to something that was read.
    property bool restored: false

    function restoreLayout() {
        // Set on every path out of here, the failures included: a file that is
        // absent or unreadable is not a reason to stop saving — it is the reason
        // there was nothing to read.
        restored = true;

        const stored = Shell.loadLayout();
        if (!stored)
            return;

        try {
            const parsed = JSON.parse(stored);

            restoring = true;
            // A file may name an arrangement this build has dropped; the one a
            // first launch opens in is the safe landing.
            const named = parsed.template || "";
            let known = named.indexOf("user:") === 0;
            for (let i = 0; i < Layouts.templates.length; i++)
                if (Layouts.templates[i].key === named)
                    known = true;
            template = known ? named : Layouts.templates[0].key;

            // Not part of an arrangement: which colours you read code in
            // survives every template switch and every Reset UI.
            codeThemePicked = parsed.codeThemePicked === true;
            if (codeThemePicked && Theme.codeThemes[parsed.codeTheme] !== undefined)
                Theme.codeTheme = parsed.codeTheme;
            Keymap.restore(parsed.keymap);

            // The trees that DO come from disk are data from another run: they
            // may name panels this build no longer has. Anything unrecognised is
            // dropped rather than trusted — an arrangement is not worth a window
            // that will not open.
            defaults = keptArrangements(parsed.defaults || ({}));
            saved = (parsed.saved || [])
                .filter((one) => one && one.name && one.tree)
                .map((one) => ({
                    name: one.name,
                    tree: sanitise(one.tree),
                    floats: one.floats || [],
                    options: one.options || ({})
                }))
                .filter((one) => one.tree);

            // No arrangement is read back: the window opens on what you DECIDED
            // it should open on. A named display opens as it was named; a
            // built-in one opens on the shape you pinned with Update default, or
            // on the shape it ships with. Whatever you bent last session was an
            // attempt, and attempts do not outlive the window that made them.
            const mine = template.indexOf("user:") === 0 ? savedIndex(template.substring(5)) : -1;
            if (mine >= 0) {
                const kept = saved[mine];
                tree = copy(kept.tree);
                floats = copy(kept.floats || []);
                mediaDisplay = kept.options && kept.options.mediaDisplay === "list" ? "list" : "grid";
            } else {
                tree = buildTemplate(template);
                floats = buildFloats(template);
                mediaDisplay = buildOptions(template).mediaDisplay === "list" ? "list" : "grid";
            }
            layouts = ({});
            nextId = highestId(tree) + 1;
            restoring = false;
        } catch (error) {
            console.warn("[dock] ignoring an unreadable saved layout:", error);
            restoring = false;
        }
    }

    // The pinned arrangements, with anything this build cannot draw taken out.
    function keptArrangements(stored) {
        let out = ({});
        for (const key in stored) {
            const one = stored[key];
            if (!one || !one.tree)
                continue;
            const shape = sanitise(copy(one.tree));
            if (!shape)
                continue;
            out[key] = { tree: shape, floats: one.floats || [], options: one.options || ({}) };
        }
        return out;
    }

    // ── The menu bar's half of the dock ───────────────────────────────────
    // The bar is Qt Widgets and knows nothing about the tree, so the chrome
    // restates the panel list whenever the dock changes.
    function menuPanels() {
        const shown = shownKeys();
        const panels = [];
        for (let i = 0; i < panelKeys.length; i++)
            panels.push({
                key: panelKeys[i],
                label: panelTitles[panelKeys[i]],
                shown: shown.indexOf(panelKeys[i]) >= 0
            });
        return panels;
    }

    function menuTemplates() {
        const entries = [];
        for (let i = 0; i < Layouts.templates.length; i++)
            entries.push({
                key: Layouts.templates[i].key,
                label: Layouts.templates[i].label,
                current: Layouts.templates[i].key === template
            });
        return entries;
    }

    // The legend, in the order it should be read: what a thing IS, what is being
    // done to it, what is happening now, and how it went. The colours come from
    // Theme so the guide cannot drift from what the panels paint.
    function guideColors() {
        return [
            // Read from the simplest thing the engine can make towards the
            // richest: a shape it draws itself, then a still, then a still with
            // time in it, then time with a picture AND sound. Each line adds one
            // thing to the one above.
            { section: "The medium" },
            { label: "polygon", meaning: "a shape the engine draws", color: panelHue("polygon") },
            { label: "image", meaning: "a still — png, svg", color: panelHue("image") },
            { label: "sound", meaning: "audio on its own", color: panelHue("sound") },
            { label: "video", meaning: "a picture with its sound, as one clip", color: panelHue("video") },
            { label: "subs", meaning: "text derived from a track, so it borrows the neutral", color: panelHue("subs") },

            { section: "Done to the medium" },
            { label: "effect", meaning: "the host's complement — an effect is not a smaller medium", color: Theme.fxKind["video"] },

            { section: "Now" },
            { label: "live", meaning: "the playhead, and whatever is about to happen", color: Theme.live },
            { label: "agent", meaning: "what the agent said or did", color: Theme.ai },

            { section: "How it went" },
            { label: "ok", meaning: "compiled, rendered, saved", color: Theme.ok },
            { label: "warn", meaning: "stale — the picture is behind the buffer", color: Theme.warn },
            { label: "bad", meaning: "it failed, and the reason is shown", color: Theme.bad }
        ];
    }

    function panelHue(kind) {
        return Theme.kind[kind];
    }

    function menuDisplays() {
        const entries = [];
        for (let i = 0; i < saved.length; i++)
            entries.push({ name: saved[i].name });
        return entries;
    }

    onTreeChanged: { Shell.setDockPanels(menuPanels()); refreshCodeShown(); }
    onFloatsChanged: { Shell.setDockPanels(menuPanels()); refreshCodeShown(); }

    // Ticking a panel that is already open closes it, exactly as its × does:
    // the menu is a view of the same state, not a second way to reach it.
    function togglePanel(key) {
        if (shownKeys().indexOf(key) >= 0)
            closeTab(firstSlotId(), key);
        else
            openPanel(key, firstSlotId());
    }

    Connections {
        target: Shell
        function onDockPanelToggled(key) { app.togglePanel(key); }
        function onDockResetRequested() { confirmReset.ask(); }
        function onDockTemplateChosen(key) { app.useTemplate(key); }
        function onDockDisplayChosen(name) { app.loadDisplay(name); }
        function onDockSaveRequested() { saveDisplay.ask(); }
        function onDockDefaultRequested() { app.updateDefault(); }
        function onDockMeasureRequested() { app.measuring = true; }
        // Opening a scene is one call: the pane loads it, the analyser is told
        // about it, and the window's idea of "the scene" moves with it.
        function onSceneOpened(path) { app.openScene(path); }

        function onMediaDropped(path) {
            const kind = app.kindOfFile(path);
            if (kind === "")
                return;
            app.addedAssets = app.addedAssets.concat([{ n: path.split("/").pop(), kind: kind, path: path }]);
            app.insertMedia(path, kind);
        }

        // A folder changes what the analyser considers the project, and a
        // server's root is fixed at initialize — so this is a new process.
        function onFolderOpened(folder, path) {
            Lsp.restart(folder);
            // The agent is told the same thing for the same reason: what it may
            // read and write is the project, and the project just changed.
            Agent.setRoot(folder);
            app.openScene(path);
        }

        function onSettingsRequested() { settings.visible = true; }
        function onCodeThemeChosen(key) { app.useCodeTheme(key); }
        function onShortcutsRequested() { shortcuts.visible = true; }
    }

    // The code pane's palette. Kept with the dock's options rather than with the
    // arrangement: which colours you read code in is about you, not about which
    // template you happen to be in.
    // Whether the palette on screen is a CHOICE or just the default of the day.
    // Without it, a default that changes cannot reach anyone who has ever saved
    // a layout: the old default was written to disk and would look like a
    // decision nobody made.
    property bool codeThemePicked: false

    function openScene(path) {
        scenePath = path;
        // The one file `Agent.revert()` can put back. Told here rather than at
        // startup, because it changes every time a scene is opened.
        Agent.watch(path);
        source.load(path);
        sentText = source.text;
        // Opening a file IS an execute. The rule that the timeline only moves on
        // ⌘R is about edits — it stops the picture flickering under your typing
        // — and it was never meant to leave a freshly opened scene represented
        // by nothing.
        executeScene();
        // The pane may be behind another tab — opening a file and not showing
        // it is the kind of silence this dock is built to avoid.
        showPanel("code");
        Qt.callLater(source.takeFocus);
    }

    function showPanel(key) {
        const slot = slotHolding(key);
        if (slot === -1) {
            openPanel(key, firstSlotId());
            return;
        }
        const next = copy(tree);
        const hit = findNode(next, slot);
        if (hit) {
            hit.node.current = Math.max(0, hit.node.keys.indexOf(key));
            tree = next;
            saveLayout();
        }
    }

    function slotHolding(key, node) {
        const here = node !== undefined ? node : tree;
        if (here.t === "s")
            return here.keys.indexOf(key) >= 0 ? here.id : -1;
        for (const child of (here.nodes || [])) {
            const found = slotHolding(key, child);
            if (found !== -1)
                return found;
        }
        return -1;
    }

    function useCodeTheme(key) {
        Theme.codeTheme = key;
        codeThemePicked = true;
        Shell.setCodeThemes(menuCodeThemes());
        saveLayout();
    }

    function menuCodeThemes() {
        let out = [];
        for (const key in Theme.codeThemes)
            out.push({ key: key, label: Theme.codeThemes[key].label, current: key === Theme.codeTheme });
        return out;
    }

    // Reset UI puts the CURRENT template back to how it ships and forgets your
    // version of it. The other templates are untouched: resetting the one you
    // are looking at should not cost you the two you are not.
    function resetLayout() {
        // A saved display resets to what was saved under its name; a built-in
        // one resets to how it ships — or to the shape you saved OVER it, which
        // is then the one it ships with as far as this dock is concerned.
        if (template.indexOf("user:") === 0) {
            const name = template.substring(5);
            template = "";
            loadDisplay(name);
            return;
        }

        const kept = copy(layouts);
        delete kept[template];
        layouts = kept;
        floats = buildFloats(template);
        tree = buildTemplate(template);
        mediaDisplay = buildOptions(template).mediaDisplay;
        saveLayout();
    }

    // ── The language server ───────────────────────────────────────────────
    // Started with the window rather than with the pane: it takes a moment to
    // index a project, and nothing is gained by making that wait visible.
    property string scenePath: ""

    Connections {
        target: Lsp

        function onReady(capabilities) {
            // One line, and a count rather than the roll-call: twenty-one
            // provider names wrapped over three terminal lines every launch,
            // and the only thing anyone reads there is whether it came up.
            console.log("[lsp] ready —", capabilities.length, "providers");
            if (source.path.length > 0) {
                Lsp.openDocument(source.path, source.text);
                colouring.restart();
            }
        }

        function onFailed(why) {
            console.warn("[lsp]", why);
        }

        // Diagnostics arrive for every file the server has looked at, not only
        // the one on screen — following a definition into videocode/ makes it
        // check that module too. Only the pane's current file is drawn.
        // What each name IS, from the analyser. Asked for once the file settles
        // rather than on every keystroke: it costs a walk of the whole file, and
        // the lexical colouring underneath is already correct while you type.
        function onTokens(path, spans) {
            if (path === source.path && source.document !== null)
                Shell.applySemanticTokens(source.document, spans);
        }

        function onDiagnostics(path, items) {
            if (path !== source.path)
                return;
            // Not printed. The analyser answers on every pause in typing, so
            // this wrote a line per keystroke-and-a-half into the terminal the
            // window was launched from — hundreds of them in a session, none of
            // which anyone reads. What it had to say is already on screen: the
            // squiggle, the gutter mark, and the count in the status strip.
            source.diagnostics = items;
        }
    }

    Component.onCompleted: {
        // The scene is a file on disk before it is anything else: a language
        // server reasons about files, and so does every jump to a definition.
        scenePath = Shell.scenePath();
        effectNames = Shell.effects();
        // Asked for only if this binary has it. The chrome is QML read from
        // disk and reloads on save; the shell behind it does not, so a window
        // started from a binary built before a bridge existed meets a call that
        // is not there — and an exception here stops the WHOLE of this block,
        // which is the line that loads the scene. One missing panel is a
        // nuisance; an editor that opens empty looks broken.
        templateNames = Shell.templates !== undefined ? Shell.templates() : [];

        // Asked once, at the top: the setting is a preference about the whole
        // window, and re-reading it per animation would be a system call in the
        // middle of every fade.
        Theme.reducedMotion = Shell.reducedMotion();

        Lsp.start(Shell.projectRoot());
        Agent.setRoot(Shell.projectRoot());
        if (scenePath.length > 0) {
            Agent.watch(scenePath);
            source.load(scenePath);
            sentText = source.text;
            // Nothing takes the caret here. The five transport keys and the
            // editor's five are the same five, and whoever holds the caret wins
            // them — so handing it to the pane at launch made Space write a
            // space in a window whose first gesture is almost always to play.
            // The pane takes it when you click in it, open a file, or follow a
            // definition, which are the moments you meant to type.
            //
            // One tick later, so the window is on screen before a
            // scene that takes 200 ms to run gets to hold it there.
            Qt.callLater(app.executeScene);
        }

        restoreLayout();

        // Filled in the order the menus are meant to READ in, left to right.
        // Qt's Cocoa bridge inserts a menu into the bar when it first gets
        // contents, not when it was declared — so the order these calls run in
        // is the order the titles end up in.
        Shell.setCodeThemes(menuCodeThemes());
        Shell.setDockPanels(menuPanels());
        Shell.setDockTemplates(menuTemplates());
        Shell.setDockDisplays(menuDisplays());
        // The legend never changes, so it is filled once and then owned by the
        // menu bar.
        Shell.setGuideColors(guideColors());
    }

    // ── The ⋯ menu ────────────────────────────────────────────────────────
    property string menuSlot: ""

    function openMenu(id, x, y) {
        menuSlot = id;

        const shown = shownKeys();
        const entries = [];
        for (let i = 0; i < panelKeys.length; i++) {
            const key = panelKeys[i];
            entries.push({
                kind: "check",
                on: shown.indexOf(key) >= 0,
                label: panelTitles[key],
                act: "toggle",
                key: key
            });
        }

        const here = slotOf(id);
        const currentKey = here && here.keys.length > 0 ? here.keys[here.current] : "";

        // What a panel can be asked, asked of the panel you are looking at. Only
        // the bin has anything to say so far, and the submenu exists so the next
        // panel with an opinion has somewhere to put it.
        if (currentKey === "media") {
            entries.push({ kind: "rule" });
            entries.push({
                kind: "sub",
                label: "Display",
                sub: [
                    { kind: "check", on: mediaDisplay === "grid", label: "Grid",
                      act: "media-display", value: "grid" },
                    { kind: "check", on: mediaDisplay === "list", label: "Details",
                      act: "media-display", value: "list" }
                ]
            });
        }

        if (currentKey !== "") {
            entries.push({ kind: "rule" });
            entries.push({
                kind: "item",
                label: "Float " + panelTitles[currentKey],
                act: "float",
                key: currentKey
            });
        }

        if (hasSpaceBeside(id)) {
            entries.push({ kind: "rule" });
            entries.push({ kind: "item", label: "Remove space", act: "remove-space" });
        }

        entries.push({ kind: "rule" });
        entries.push({ kind: "item", label: "Save display…", act: "save-display" });

        const displays = [];
        for (let i = 0; i < saved.length; i++)
            displays.push({
                kind: "check",
                on: template === "user:" + saved[i].name,
                label: saved[i].name,
                act: "load-display",
                value: saved[i].name
            });
        if (displays.length === 0)
            displays.push({ kind: "item", label: "Nothing saved yet", act: "" });
        entries.push({ kind: "sub", label: "Load display", sub: displays });

        entries.push({ kind: "item", label: "Reset UI", act: "reset", key: "" });

        menu.entries = entries;
        const local = menu.mapFromGlobal(x, y);
        menu.popup(local.x, local.y);
    }

    function runMenu(entry) {
        if (!entry)
            return;

        if (entry.act === "") {
            return;
        } else if (entry.act === "reset") {
            // Never straight through: this one throws away work.
            confirmReset.ask();
        } else if (entry.act === "remove-space") {
            removeSpace(menuSlot);
        } else if (entry.act === "save-display") {
            saveDisplay.ask();
        } else if (entry.act === "load-display") {
            loadDisplay(entry.value);
        } else if (entry.act === "media-display") {
            mediaDisplay = entry.value;
            saveLayout();
        } else if (entry.act === "float") {
            const at = app.paneCentre(menuSlot);
            floatTab(entry.key, at.x, at.y);
        } else if (shownKeys().indexOf(entry.key) >= 0) {
            closeTab(menuSlot, entry.key);
        } else {
            openPanel(entry.key, menuSlot);
        }
    }

    // ── No title bar of our own ───────────────────────────────────────────
    // The window already has one, drawn by the system, and a second strip under
    // it was spending 36 px of every screen on a brand nobody needs to be told
    // twice. What it also carried — the scene's name — was a promise the editor
    // does not keep: a scene need not come from a .py file at all, since the
    // buffer IS the scene and an empty one is a legitimate way to start. The
    // name belongs where the buffer is, on the Code panel's own bar, which shows
    // it beside whether it is compiled and whether it differs from the last save.

    // ── Dock ──────────────────────────────────────────────────────────────
    DockCanvas {
        id: dockArea
        anchors {
            left: parent.left; right: parent.right
            top: parent.top; bottom: status.top
            margins: Theme.gap
        }
        // The preview while a tab is in the air, the real tree otherwise. The
        // panes are the same items either way — the canvas keeps a row per node
        // id and only moves it — so the hole opening is a re-layout of things
        // that already exist, which is exactly what makes it animate.
        // Truthiness, not `!== null`: an uninitialised property is `undefined`,
        // which is not null — so at startup this handed the canvas `undefined`
        // and the dock came up empty and STAYED empty, because the binding then
        // depended on a property nothing was going to change.
        node: app.previewTree ? app.previewTree : app.tree
        // What the pointer is resolved against, which must not be what the
        // pointer just changed — see `hitPlan`.
        hitNode: app.tree
        dock: app
    }

    // The dock's own edge, shown while a tab is in the air: a band you cannot
    // see is a band nobody finds, and "drop here for a row across the window" is
    // not a thing you guess. Where it would LAND is not drawn here — the hole
    // that opens in the layout says that better than any rectangle could.
    Item {
      anchors.fill: dockArea
      z: 199

      Repeater {
        model: app.tabInFlight ? ["left", "right", "top", "bottom"] : []

        Rectangle {
            required property var modelData
            readonly property bool across: modelData === "left" || modelData === "right"
            x: modelData === "right" ? parent.width - app.dockBand : 0
            y: modelData === "bottom" ? parent.height - app.dockBand : 0
            width: across ? app.dockBand : parent.width
            height: across ? parent.height : app.dockBand
            color: "transparent"
            border.width: 1
            border.color: app.hoverZone === modelData && app.hoverSlot === app.wholeDock
                          ? Theme.live : Qt.alpha(Theme.live, 0.22)
            radius: Theme.radiusInner

            Behavior on border.color { ColorAnimation { duration: Theme.motion(120) } }
        }
      }
    }

    StatusStrip {
        id: status
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        inputCount: app.shownScene.elements.length
        compileMs: 84
        frameMs: 11.4
        execState: app.execState
        execStale: app.execStale
        execMs: app.execMs
    }

    SettingsPanel {
        id: settings
        anchors.fill: parent
        z: 320
        mediaDisplay: app.mediaDisplay
        onCodeThemePicked: (key) => app.useCodeTheme(key)
        onMediaDisplayPicked: (key) => { app.mediaDisplay = key; app.saveLayout(); }
        onResetRequested: confirmReset.ask()
    }

    // ── Dropping a file on the window ─────────────────────────────────────
    // A file dragged from the Finder becomes a LINE OF CODE at the caret, and a
    // row in the bin. Anything else would be a lie about where a scene lives:
    // there is no hidden project model behind this editor, only the buffer, so
    // "adding" a video has to be a statement you can read and delete.
    //
    // This is an insertion, not a rewrite — the councils refused rewriting an
    // existing call, and this touches nothing that was already written.
    DropArea {
        anchors.fill: parent
        z: 400
        keys: ["text/uri-list"]

        onDropped: (drop) => {
            let added = [];
            for (const url of drop.urls) {
                const path = url.toString().replace("file://", "");
                const kind = app.kindOfFile(path);
                if (kind === "")
                    continue;
                added.push({ n: path.split("/").pop(), kind: kind, path: path });
                app.insertMedia(path, kind);
            }
            if (added.length === 0)
                return;
            app.addedAssets = app.addedAssets.concat(added);
            drop.accept();
        }

        Rectangle {
            anchors.fill: parent
            visible: parent.containsDrag
            color: Qt.alpha(Theme.live, 0.06)
            border.width: 2
            border.color: Theme.live
        }
    }

    // The statement a dropped file becomes. Named after the file so the line
    // reads as a sentence, and inserted on its own line above the caret's —
    // never in the middle of whatever you were typing.
    function insertMedia(path, kind) {
        const cls = kind === "video" ? "Video" : (kind === "image" ? "Image" : "Sound");
        source.insertLine(app.nameFromFile('"' + path + '"')
                          + " = " + cls + '("' + app.projectRelative(path) + '")');
        showPanel("code");
    }

    // A Python name out of a file name: what is between the last slash and the
    // first dot, with anything that cannot be in a name taken out. `interview =
    // Video("interview.mp4")` is what a person writes; `video2` is what a tool
    // writes.
    function nameFromFile(lead) {
        const quoted = /^["'](.*)["']$/.exec(lead.trim());
        if (quoted === null)
            return "";
        const base = quoted[1].split("/").pop().split(".")[0].replace(/[^A-Za-z0-9_]/g, "_");
        return /^[A-Za-z_]/.test(base) ? base : "clip" + base;
    }

    // The clip you opened, in the middle of the window.
    ElementCard {
        id: elementCard
        anchors.fill: parent
        z: 310
        effectNames: app.effectNames
        onEffectRequested: (element, effect, options) => app.applyEffect(element, effect, options)
        onMemberOpened: (member, where) => elementCard.open(member, where)
        // Reading the source is the card's own business — `Shell` is in scope
        // everywhere. Writing goes through the shell so the scene re-runs, which
        // is what makes the gesture visible.
        onArgumentWritten: (element, call, name, value) => app.writeArgument(element, call, name, value)
        buffer: source.text
        onJumpRequested: (element) => app.revealLine(element.line)
        // An effect row answers for the call that wrote it: the ✕ deletes that
        // call, a drag rewrites its `start` or `duration`, a click goes to it.
        onEffectRemoved: (fx) => app.removeCall(fx.line, fx.call)
        onEffectWritten: (fx, name, value) => {
            // No name means the card would not do the arithmetic: the argument
            // is written as an expression, and rewriting `RATIO * 0.5` as `0.6`
            // would answer a drag by deleting a decision.
            if (name.length === 0)
                source.say(fx.call + " is written as an expression — edit the line itself");
            else
                app.writeOn(fx.line, fx.call, name, value);
        }
        onEffectJumped: (fx) => app.revealLine(fx.line)
        onEffectToggled: (line, off) => app.toggleLine(line, off)
    }

    // What is being carried, under the pointer. Small and out of the way: the
    // thing you are aiming at is the timeline, and a big label over it would
    // hide the moment you are trying to pick.
    Rectangle {
        visible: app.carried !== null
        z: 340
        x: (app.carried !== null ? app.carried.x : 0) + 14
        y: (app.carried !== null ? app.carried.y : 0) + 14
        width: ghost.implicitWidth + 16
        height: 22
        radius: 4
        color: Theme.live
        opacity: 0.92

        Text {
            id: ghost
            anchors.centerIn: parent
            text: app.carried !== null ? app.carried.template.name : ""
            color: "#0b1018"
            font.family: Theme.mono
            font.pixelSize: 11
            font.weight: Font.DemiBold
        }
    }

    ShortcutsPanel {
        id: shortcuts
        anchors.fill: parent
        z: 320
    }

    // The click that ends the measuring. Over every pane so nothing else can
    // take it — the panes are showing numbers rather than working, and a click
    // that landed on one of them would have to mean two things at once.
    MouseArea {
        anchors.fill: parent
        z: 330
        visible: app.measuring
        acceptedButtons: Qt.AllButtons
        onPressed: app.measuring = false
    }

    // The figure under your hand while a pane is being resized. Drawn at the
    // window's level rather than inside the pane: a label that belongs to a
    // splitter is on the boundary of two panes, and inside either one it would be
    // clipped away by the very edge you are dragging.
    Rectangle {
        id: tipBox
        z: 340
        visible: app.tip !== null
        width: tipText.implicitWidth + 14
        height: tipText.implicitHeight + 8
        // Ahead of the pointer, and pulled back inside the window at the edges —
        // the reading you want is the one you get while dragging TOWARDS an edge.
        x: app.tip !== null ? Math.max(4, Math.min(app.tip.x + 14, app.width - width - 4)) : 0
        y: app.tip !== null ? Math.max(4, Math.min(app.tip.y + 16, app.height - height - 4)) : 0
        color: Theme.rail
        radius: Theme.radiusSmall
        border.width: 1
        border.color: Theme.live

        Text {
            id: tipText
            anchors.centerIn: parent
            text: app.tip !== null ? app.tip.text : ""
            color: Theme.ink
            font.family: Theme.mono
            font.pixelSize: 11
        }
    }

    // Re-asked after the typing stops. The tokens are positions in a file that
    // is still being edited, so asking mid-word would paint yesterday's answer
    // onto today's text.
    // The buffer as the server last saw it.
    property string sentText: ""

    // ── Executing the scene ───────────────────────────────────────────────
    // Only ⌘R runs it, and that is not a performance decision.
    //
    // A scene is arbitrary Python whose constructors open files. Running it on
    // a pause in typing means running unfinished text ten to thirty times a
    // minute, and the compile gate does not save you: `wait(1)` mid-keystroke is
    // `wait(11)` — syntactically perfect, semantically another film, executed
    // for real. You can debounce a question; you cannot debounce a side effect.
    //
    // The cost of the choice is that the picture is behind the buffer, and the
    // whole of `execState` exists so that is visible rather than assumed.
    property string execText: ""
    property string execState: "none"   // none · fresh · stale · failed
    property real execMs: 0
    property int execInputs: 0
    property int execFrames: 0
    property int execFps: 30

    // Bumped by every successful run. The preview draws frame N of a scene, and
    // "frame 12" means a different picture once the buffer has been executed
    // again — without this the pane would keep showing the old scene at the new
    // playhead, which is the one lie a preview must not tell.
    property int execRevision: 0

    readonly property bool execStale: execState !== "none" && source.text !== execText

    // ── The scene the timeline draws ──────────────────────────────────────
    // Built from what the last ⌘R actually made, in the shape the timeline
    // already speaks. Empty until a run has happened, and the panel falls back
    // to the stand-in scene so the dock still has something to lay out.
    //
    // Elements are grouped by their CALL SITE: one `Text("GRADIENT")` is eight
    // Polygon inputs from one line, and eight bars for one word is not a
    // timeline, it is a leak of the engine's internals. A row with members is a
    // group; clicking it opens them.
    property var liveScene: null

    readonly property var shownScene: liveScene !== null ? liveScene : emptyScene

    // The bin holds what the SCENE loads, plus what has been dropped this
    // session. Same rule as the timeline: it comes from the code, or it is not
    // there. `Video`, `Image` and `Sound` are the inputs that read a file; a
    // Rectangle is not media however it is drawn.
    readonly property var sceneAssets: {
        const out = [];
        const seen = ({});
        for (const one of shownScene.elements) {
            if (one.kind !== "video" && one.kind !== "image" && one.kind !== "sound")
                continue;
            if (seen[one.n] === true)
                continue;
            seen[one.n] = true;
            // Where the file IS, read off the call that loaded it. Without it a
            // clip already in the scene could be shown in the bin and not
            // dragged out of it — and "the bin" would mean two different things
            // depending on which row you had your hand on.
            const path = one.line > 0
                       ? Shell.readPositional(source.text, one.line, one.cls, 0) : "";
            out.push({ n: one.n, kind: one.kind, lead: path, line: one.line });
        }
        return out;
    }

    function kindOf(cls) {
        if (cls === "Video") return "video";
        if (cls === "Image") return "image";
        if (cls === "Sound") return "sound";
        // `Text` is drawn by the engine, so it is a polygon like any other
        // shape. The palette's `subs` hue means text DERIVED from a track —
        // a transcription — and giving it to a title would say the wrong thing
        // in the one place the colour is supposed to be the explanation.
        return "polygon";
    }

    // The name the author gave it, read off the line that made it: `square =
    // Square(...)` is called `square` everywhere else in their file, so calling
    // it "Square" here would be the tool renaming their work.
    function labelFor(element) {
        const lines = source.text.split("\n");
        const line = element.line >= 1 && element.line <= lines.length
                   ? lines[element.line - 1] : "";
        const named = /^\s*([A-Za-z_]\w*)\s*=/.exec(line);
        return named !== null ? named[1] : element.kind;
    }

    // A part of a folded row, numbered. They all come from one line, so they all
    // carry the same name — and eight rows called `title` name nothing. The
    // ordinal is the letter's place in the word, which is the only thing that
    // tells them apart.
    function partOf(element, ordinal) {
        return {
            n: element.n + " " + ordinal,
            kind: element.kind,
            l: element.l,
            d: element.d,
            line: element.line,
            index: element.index,
            cls: element.cls,
            points: element.points,
            effects: element.effects,
            members: []
        };
    }

    function buildLiveScene(model) {
        const fps = model.fps;
        // Where the scene's time joins. A `wait()` is the only place the
        // language lets a change push what follows, so the timeline draws them
        // rather than inventing a rule of its own about what ripples.
        // A gap is exactly the frames it was written as. It reaches the end of
        // the scene on its own when nothing follows — no special case here —
        // because the scene is now as long as the video it makes.
        const waits = (model.waits || []).map((w) => ({
            at: w.start / fps,
            d: w.frames / fps,
            says: w.frames / fps,
            line: w.line
        }));
        let rows = [];
        let byLine = ({});

        for (const element of model.elements) {
            const one = {
                n: labelFor(element),
                kind: kindOf(element.kind),
                l: element.first / fps,
                d: (element.last - element.first + 1) / fps,
                line: element.line,
                // The class the scene actually named — `Square`, `Video` — kept
                // beside the media kind it is drawn as. A gesture writes to the
                // CALL, and the call is spelled with this.
                cls: element.kind,
                index: element.index,
                // The lines that already say something about this element, and
                // the cursor each one leaves behind. What a gesture needs to
                // write a NEW statement — see trimElement.
                points: element.points !== undefined ? element.points : [],
                // Named by what the SCENE says, not by what the renderer
                // calls it: a row that reads `scaleTo` is talking about the
                // line you wrote, and a row that reads `Scale` is talking
                // about a shader you never asked about. `kinds` keeps the
                // shaders behind it, for the tooltip.
                effects: element.effects.map((fx) => ({
                    n: fx.call !== undefined && fx.call.length > 0 ? fx.call : fx.name,
                    l: fx.start / fps,
                    d: (fx.end - fx.start + 1) / fps,
                    call: fx.call !== undefined ? fx.call : "",
                    line: fx.line !== undefined ? fx.line : 0,
                    kinds: fx.kinds !== undefined ? fx.kinds : [fx.name]
                })),
                members: []
            };

            // Same line, same gesture: fold it in rather than adding a row.
            const key = element.file + ":" + element.line;
            if (element.line > 0 && byLine[key] !== undefined) {
                const parent = rows[byLine[key]];
                // The row IS the first part, so it joins the list the first
                // time a second one shows up — otherwise a word of eight
                // letters reports seven.
                if (parent.members.length === 0)
                    parent.members.push(partOf(parent, 1));
                parent.members.push(partOf(one, parent.members.length + 1));
                parent.l = Math.min(parent.l, one.l);
                parent.d = Math.max(parent.d, one.l + one.d - parent.l);
                continue;
            }
            byLine[key] = rows.length;
            rows.push(one);
        }

        return { duration: model.frames / fps, elements: rows, waits: waits };
    }

    // Every effect the library exposes, asked for once.
    property var effectNames: []

    // And everything it can build: shapes, media, templates.
    property var templateNames: []

    // The two catalogues as one list, which is what the Library panel shows.
    //
    // They are different in kind — a template IS an element, an effect happens
    // TO one — and the panel says so by where a thing can be dropped, not by
    // making you look in two places for "what can I add".
    readonly property var placeable: {
        const out = [];
        for (const template of templateNames)
            out.push(template);
        for (const effect of effectNames)
            out.push({
                name: effect.name,
                group: "effect",
                module: effect.module,
                form: effect.form,
                says: "",
                params: effect.params,
                required: []
            });
        return out;
    }

    // What is being carried across the window right now — {template, values,
    // x, y} — or null. The ghost under the pointer is drawn from it, and so is
    // the timeline's mark of where it would land.
    property var carried: null

    function carryTemplate(template, values, x, y) {
        carried = { template: template, values: values, x: x, y: y };
        timeline.dropAt = timeline.timeAtWindow(x, y);
        // An effect needs a clip under it; a template needs only a moment. Both
        // are shown while the thing is in the air, because a drop you cannot aim
        // is a drop you undo.
        const over = template.group === "effect" ? timeline.elementAtWindow(x, y) : null;
        timeline.hoverLane = over === null ? -1 : timeline.scene.elements.indexOf(over);
    }

    // ── A file, from the bin onto the timeline ────────────────────────────
    // The same gesture as a template, with the file as the call's first
    // argument. Which class it is comes from the KIND the bin already knows —
    // a bin that can show you a sound and then write `Video(...)` about it is a
    // bin that has stopped being about your files.
    function carryAsset(asset, x, y) {
        carried = { template: { name: app.classOf(asset.kind), group: "media" }, values: ({}), x: x, y: y };
        timeline.dropAt = timeline.timeAtWindow(x, y);
        timeline.hoverLane = -1;
    }

    function classOf(kind) {
        if (kind === "video") return "Video";
        if (kind === "sound") return "Sound";
        if (kind === "image") return "Image";
        return "Video";
    }

    function dropAsset(asset, x, y) {
        const at = timeline.timeAtWindow(x, y);
        carried = null;
        timeline.dropAt = -1;
        timeline.hoverLane = -1;

        if (at < 0) {
            source.say("drop it on the timeline, at the moment it should appear");
            return;
        }

        // What the call needs to name the file. A row that came from the bin
        // carries a path; a row that came from the scene carries the very text
        // the existing call uses, quotes and all.
        const lead = asset.lead !== undefined && asset.lead.length > 0
                   ? asset.lead
                   : '"' + app.projectRelative(asset.path !== undefined ? asset.path : "") + '"';
        if (lead === '""') {
            source.say("that row has no file behind it");
            return;
        }

        placeTemplate({ name: app.classOf(asset.kind), module: "", params: [], required: [] },
                      ({}), app.snapTime(at, false),
                      { lead: lead, name: app.nameFromFile(lead) });
    }

    // Relative to the project when it is inside it: an absolute path is a scene
    // that only renders on this machine.
    function projectRelative(path) {
        const root = Shell.projectRoot() + "/";
        return path.indexOf(root) === 0 ? path.substring(root.length) : path;
    }

    function dropTemplate(template, values, x, y) {
        const at = timeline.timeAtWindow(x, y);
        const over = timeline.elementAtWindow(x, y);
        carried = null;
        timeline.dropAt = -1;
        timeline.hoverLane = -1;

        if (template.group === "effect") {
            if (over === null || at < 0) {
                source.say("an effect goes on a clip — drop it on one");
                return;
            }
            app.applyEffect(over, template, { values: values, at: app.snapTime(at, false) });
            return;
        }

        if (at < 0) {
            // Dropped on nothing. Better than dropping it at the caret: a
            // template that lands wherever the cursor happens to be is a line
            // you did not place.
            source.say("drop it on the timeline, at the moment it should appear");
            return;
        }
        placeTemplate(template, values, app.snapTime(at, false));
    }

    // Applying an effect is an INSERTED statement, never a rewritten one.
    //
    // `square.apply(fadeIn())` on its own line says exactly what happened, can
    // be read, moved and deleted, and leaves every call you wrote untouched.
    // Editing an existing call — adding an argument, changing a duration — is
    // the thing three councils refused, because it needs to be right about code
    // it did not write.
    // A gesture writes to the line that made the element.
    //
    // Not a line appended at the end: the timeline is a VIEW of the source, so
    // moving something in the view has to be the same edit a person would have
    // typed. `Shell.setArgument` finds the call by line and name and replaces
    // that value's characters — the rest of the file, comments and spacing
    // included, is what it was.
    //
    // The scene is re-run straight after, because a gesture whose result you
    // have to ask for with ⌘R is not a gesture.
    function writeArgument(element, call, name, value) {
        if (element === null || element.line === undefined || element.line <= 0)
            return false;

        // As a range applied to the pane's own document, so the gesture is in
        // the same undo history as typing — see SourcePanel.replaceRange.
        const span = Shell.argumentSpan(source.text, element.line, call, name, value);
        if (!span.ok) {
            source.say("could not write " + name);
            return false;
        }

        if (!source.replaceRange(span.start, span.end, span.text))
            return false;

        app.executeScene();
        return true;
    }

    // The same edit, addressed by line rather than by element: an effect knows
    // the call that wrote it and nothing else about the element it animates.
    function writeOn(line, call, name, value) {
        if (line === undefined || line <= 0 || call === undefined || call.length === 0)
            return false;

        const span = Shell.argumentSpan(source.text, line, call, name, value);
        if (!span.ok) {
            source.say("could not write " + name);
            return false;
        }
        if (!source.replaceRange(span.start, span.end, span.text))
            return false;

        app.executeScene();
        return true;
    }

    // Taking an effect off is deleting the call that put it on — the same edit
    // in reverse, and the reason `removeCallSpan` tells a link of a chain from a
    // statement of its own: `.rotateBy(180)` goes on its own, `square.fadeIn()`
    // takes its line with it. Refused rather than guessed when the call sits
    // inside something else, because a delete that lands on the wrong span is
    // the one gesture nobody forgives.
    function removeCall(line, call) {
        if (line === undefined || line <= 0 || call === undefined || call.length === 0)
            return false;

        const span = Shell.removeCallSpan(source.text, line, call);
        if (!span.ok) {
            source.say("could not remove " + call + " — line " + line);
            return false;
        }
        if (!source.replaceRange(span.start, span.end, span.text))
            return false;

        app.executeScene();
        source.say("removed " + call + " · ⌘Z to put it back");
        return true;
    }

    // ── Placing something new, at a moment ────────────────────────────────
    //
    // A template is not an effect: it does not act on an element, it IS one. So
    // the drop writes the line that makes it — and, when the moment asked for is
    // not the one the code has already reached, the two lines that say when it
    // appears.
    //
    // WHERE those lines go is the whole problem. A `wait()` is a barrier for
    // everything in the scene: an element created after one cannot start before
    // it, whatever it says. So the block goes before the first wait that has
    // already passed the moment wanted, and `start=` counts from the wait
    // before that. Written at the end of the file, a template could only ever
    // land after the last wait — which is to say, at the end of the video.
    function placeTemplate(template, values, seconds, options) {
        if (template === undefined || template === null)
            return;

        const fps = execFps > 0 ? execFps : 30;
        const target = Math.round(seconds * fps);

        let base = 0;
        let afterLine = source.text.split("\n").length;
        for (const gap of (liveScene.waits !== undefined ? liveScene.waits : [])) {
            const ends = Math.round((gap.at + gap.d) * fps);
            if (ends <= target) {
                base = ends;
                continue;
            }
            // The block belongs above this wait, and `insertBlock` writes after
            // a line, so it is told about the one before it.
            afterLine = Math.max(0, gap.line - 1);
            break;
        }

        // A name nothing else in the scene has. The class in lower case is what
        // a person writes nine times out of ten; the number only appears when it
        // has to.
        // Named after the FILE when there is one — `interview = Video("interview.mp4")`
        // is what a person writes, and `video2` is what a tool writes.
        const wanted = options && options.name ? options.name : "";
        const stem = wanted.length > 0
                   ? wanted
                   : template.name.charAt(0).toLowerCase() + template.name.slice(1);
        let name = stem;
        for (let n = 2; new RegExp("^\\s*" + name + "\\s*[.=]", "m").test(source.text); ++n)
            name = stem + n;

        // Only what was actually decided: a field left at the signature's own
        // default is not written. The day a default changes, every scene that
        // spelled it out keeps the old one without saying so.
        const args = [];
        for (const parameter of template.params) {
            const written = values[parameter.name];
            if (written === undefined)
                continue;
            const value = String(written).trim();
            if (value.length === 0 || value === parameter.value)
                continue;
            args.push(parameter.name + "=" + value);
        }

        // A file goes in the first slot, with no name in front of it — that is
        // how `Video("shot.mp4")` reads, and the editor writes what a person
        // would have typed.
        const lead = options && options.lead ? [options.lead] : [];
        const statements = [name + " = " + template.name + "(" + lead.concat(args).join(", ") + ")"];
        const moment = (target - base) / fps;
        if (moment > 0.001) {
            // Hidden, then shown: an input is on screen from the moment it
            // exists, and a template dropped at two seconds that flashes at zero
            // is not what anybody dragged.
            statements.push(name + ".hide()");
            statements.push(name + ".show(start=" + app.plain(moment) + ")");
        }

        // The block first, the import after it: an import is written at the top
        // of the file and moves every line under it by one, including the one
        // the block was measured against.
        if (!source.insertBlock(afterLine, statements))
            return;
        if (template.module.length > 0) {
            const line = "from " + template.module + " import " + template.name;
            if (source.text.indexOf(line) < 0)
                source.insertImport(line);
        }
        app.executeScene();
        source.say(name + " at " + (target / fps).toFixed(1) + "s");
    }

    // ── Trimming: where a clip stops ──────────────────────────────────────
    //
    // One meaning for every kind, because the timeline only ever draws one
    // thing: when the element is ON SCREEN. Pulling the right edge in says "stop
    // showing it here", and the only line that says that is `hide`.
    //
    // A video's `startFrame`/`endFrame` are NOT that, which is worth writing
    // down: they choose which frames of the file get loaded, and a clip whose
    // media runs out keeps its place in the scene either way — a `Video` cut to
    // thirty frames inside a three-second scene is still reported as lasting
    // three seconds. Writing `endFrame` from this gesture would have moved
    // nothing on the timeline. The frame range stays where it belongs, on the
    // card, beside the rest of the call.
    function trimElement(element, edge, seconds) {
        if (element === null || element.line === undefined || element.line <= 0)
            return;
        hideAt(element, seconds);
    }

    // Where a statement about this element has to go if it is to happen at a
    // given frame, and what its `start=` must then say.
    //
    // `start` is seconds after the element's OWN cursor, and the cursor is
    // nowhere in the buffer — it is what the lines above have left it at. So the
    // scene reports, per element, every line that already touched it and where
    // its cursor stood afterwards; a new statement goes under the last of those
    // that has not gone past the moment asked for, and counts from there.
    //
    // `null` when the moment is behind every line that could carry it, which is
    // a refusal: writing a negative `start` would schedule something before the
    // line that schedules it.
    function pointFor(element, target) {
        const fps = execFps > 0 ? execFps : 30;
        const points = element !== null && element.points !== undefined ? element.points : [];
        if (points.length === 0)
            return null;

        let chosen = points[0];
        for (const point of points)
            if (point.cursor <= target)
                chosen = point;

        const start = (target - chosen.cursor) / fps;
        return start < 0 ? null : { line: chosen.line, call: chosen.call, start: start };
    }

    // Ending an element: `square.hide(start=…)`, written where it means what it says.
    //
    // `start` is seconds after the ELEMENT's own cursor, and the cursor is
    // nowhere in the buffer — it is what the lines above have left it at. So the
    // scene reports, per element, every line that already touched it and where
    // its cursor stood afterwards; the statement goes under the last of those
    // that has not already gone past the moment asked for, and counts from
    // there. Put at the end of the file instead, it could only ever push the
    // shape's end later, never earlier.
    // `0.7`, not `0.70`: the editor writes what a person would have typed.
    function plain(value) {
        return String(Math.round(value * 100) / 100);
    }

    function hideAt(element, seconds) {
        const fps = execFps > 0 ? execFps : 30;
        const target = Math.round(seconds * fps);
        const points = element.points !== undefined ? element.points : [];
        if (points.length === 0) {
            source.say("nothing in the scene says when " + element.n + " happens");
            return;
        }

        // One end, not a queue of them: an element already told to hide is told
        // a different moment.
        for (const written of points) {
            if (written.call !== "hide")
                continue;
            const moment = (target - written.cursor) / fps;
            if (moment < 0) {
                source.say("that is before " + element.n + " reaches this line");
                return;
            }
            if (app.writeOn(written.line, "hide", "start", app.plain(moment)))
                source.say(element.n + " now ends at " + (target / fps).toFixed(1) + "s");
            return;
        }

        const where = app.pointFor(element, target);
        if (where === null) {
            source.say("that is before " + element.n + " is finished moving");
            return;
        }

        // The name has to be a name. An element built inline — `Square(...)`
        // with nothing on the left of an `=` — is called after its class here,
        // and `Square.hide()` is a statement about the class.
        const lines = source.text.split("\n");
        const declaration = element.line <= lines.length ? lines[element.line - 1] : "";
        if (!new RegExp("^\\s*" + element.n + "\\s*=").test(declaration)) {
            source.say("give it a name first — " + element.cls + "(...) on its own cannot be told to hide");
            return;
        }

        if (!source.insertAfterLine(where.line, element.n + ".hide(start=" + app.plain(where.start) + ")"))
            return;
        app.executeScene();
        source.say(element.n + " now ends at " + (target / fps).toFixed(1) + "s");
    }

    // ── Off, without being gone ───────────────────────────────────────────
    // A commented-out line is how a person turns something off in a scene, and
    // it is the only way that survives being read back: the statement is still
    // there, in order, with its arguments, and the scene runs without it.
    //
    // Which is also why the card can still show it. It is not in the timeline —
    // nothing ran — so it is found by reading the buffer, not the scene.
    function toggleLine(line, off) {
        const lines = source.text.split("\n");
        if (line < 1 || line > lines.length)
            return;

        let offset = 0;
        for (let i = 0; i < line - 1; i++)
            offset += lines[i].length + 1;

        const text = lines[line - 1];
        const parts = /^(\s*)(#\s?)?(.*)$/.exec(text);
        const next = off ? parts[1] + "# " + parts[3] : parts[1] + parts[3];
        if (next === text)
            return;

        if (!source.replaceRange(offset, offset + text.length, next))
            return;
        app.executeScene();
        source.say(off ? "off — the line is still there" : "back on");
    }

    // Going to a line: the pane comes up, the caret lands on it, and the card
    // gets out of the way. Claimed with `callLater` because the pane may have
    // been behind another tab when the line was asked for.
    function revealLine(line) {
        if (line === undefined || line <= 0 || source.path.length === 0)
            return;
        source.load(source.path, line - 1, 0);
        showPanel("code");
        Qt.callLater(source.takeFocus);
        elementCard.close();
    }

    function readArgument(element, call, name) {
        if (element === null || element.line === undefined || element.line <= 0)
            return "";
        return Shell.readArgument(source.text, element.line, call, name);
    }

    // An effect is not part of `from videocode import *` — `flash` lives in
    // videocode.template.effect.other.flash — so writing the call alone would
    // hand you a scene that does not run. A core transformation needs none:
    // `square.scaleTo(...)` is a method on the element, and importing the
    // function behind it would be an import nothing in the scene uses.
    function needsImport(effect) {
        if (effect.form === "method" || effect.module.length === 0)
            return;
        const line = "from " + effect.module + " import " + effect.name;
        if (source.text.indexOf(line) < 0)
            source.insertImport(line);
    }

    function applyEffect(element, effect, options) {
        if (element === null || element.n === undefined)
            return;

        // The import first, if it is missing. Effects are not part of
        // `from videocode import *` — `flash` lives in
        // videocode.template.effect.other.flash — so writing the call alone
        // would hand you a scene that does not run.
        //
        // A core transformation needs none: `square.scaleTo(...)` is a method on
        // the element, and importing the function behind it would be an import
        // nothing in the scene uses.

        // Only what you actually decided.
        //
        // A field left at the signature's own default is not written: the call
        // would say the same thing at twice the length, and the day a default
        // changes, every scene that spelled it out keeps the old one without
        // saying so. What you typed is written exactly as you typed it — the
        // field IS the argument.
        const args = [];
        const chosen = options && options.values ? options.values : ({});
        for (const parameter of effect.params) {
            const written = chosen[parameter.name];
            if (written === undefined)
                continue;
            const value = String(written).trim();
            if (value.length === 0 || value === parameter.value)
                continue;
            args.push(parameter.name + "=" + value);
        }

        // WHEN it happens, and WHERE that has to be written.
        //
        // The moment comes in counted from the start of the scene, because that
        // is the only thing both surfaces that can drop an effect agree on — the
        // card measures from the element's left edge, the timeline from zero.
        // `start=` is then seconds after the element's own cursor on the line
        // the statement lands on, which is not the same number and is why the
        // shell places the line rather than dropping it under the caret.
        const fps = execFps > 0 ? execFps : 30;
        const at = options && options.at !== undefined ? options.at : -1;
        let where = null;
        if (at >= 0) {
            where = app.pointFor(element, Math.round(at * fps));
            if (where === null) {
                source.say("that is before " + element.n + " is ready for it");
                return;
            }
            if (where.start > 0.001)
                args.push("start=" + app.plain(where.start));
        }

        // Three ways of saying the same thing, and the effect itself decides
        // which: a method on the element, a generator handed the element and
        // splatted into `apply`, or a factory `apply` calls for you.
        const call = effect.name + "(" + args.join(", ") + ")";
        let statement;
        if (effect.form === "method")
            statement = element.n + "." + call;
        else if (effect.form === "generator")
            statement = element.n + ".apply(*" + effect.name + "("
                      + [element.n].concat(args).join(", ") + "))";
        else
            statement = element.n + ".apply(" + call + ")";

        // Under the line that leaves the cursor where the drop asked for, or —
        // when nothing said when — under the caret, which is where you were
        // looking.
        //
        // The statement goes in BEFORE the import. An import is written at the
        // top of the file, so adding it first moves every line under it by one
        // — including the one this statement was measured against, which put a
        // `flash` between a comment and the line it was written about.
        if (where !== null) {
            if (!source.insertAfterLine(where.line, statement))
                return;
            app.needsImport(effect);
            app.executeScene();
            source.say(effect.name + " at " + at.toFixed(1) + "s");
            return;
        }

        source.insertLine(statement);
        app.needsImport(effect);
        source.say("added " + effect.name + " — ⌘R to see it");
    }

    // `announce` is what separates a run you ASKED for from one the window did
    // on its own. The notice in the code pane is a receipt for a gesture — ⌘R,
    // a save — and a receipt for something nobody did is noise: the status strip
    // already carries the last run's time, permanently, at the bottom of the
    // window. A failure speaks either way; a scene that did not run is news
    // whoever started it.
    function executeScene(announce) {
        if (source.path.length === 0)
            return;

        const answer = Shell.executeScene(source.text, source.path);
        execMs = answer.ms !== undefined ? answer.ms : 0;

        if (answer.ok) {
            execText = source.text;
            execState = "fresh";
            liveScene = buildLiveScene(JSON.parse(answer.scene));
            // Anything looking at the scene has to be looking at THIS one.
            elementCard.rebind(liveScene.elements);
            execInputs = parseInt(answer.inputs);
            execFrames = parseInt(answer.frames);
            execFps = answer.fps !== undefined ? parseInt(answer.fps) : execFps;
            execRevision += 1;
            if (announce)
                source.say("ran in " + execMs.toFixed(0) + " ms · " + execInputs + " inputs");
            return;
        }

        // The last good scene stays: an emptied timeline after a typo is the
        // worst possible answer. The failure is shown where every other one is.
        execState = "failed";
        const line = parseInt(answer.line);
        const column = parseInt(answer.column);
        source.diagnostics = [{
            range: {
                start: { line: line, character: column },
                end: { line: line, character: column + 200 }
            },
            severity: 1,
            source: "execute",
            message: answer.message
        }];
        source.say(answer.message.slice(0, 60));
    }

    // What an agent turn does to the buffer, and the two keys that settle it.
    //
    // The scene is NOT run when the turn lands. The author sees the colours,
    // and running it is what accepting MEANS — which is why ⌘R does both and
    // why nothing moves in the preview until they press it.
    Connections {
        target: Agent

        function onChanged() {
            const rows = Agent.diff();
            // The merged view: what was there in red, what replaces it in green.
            // Briefly not valid Python, so the analyser is told to hold — a
            // buffer holding both sides of an edit would light up in errors that
            // describe nothing the author did.
            let merged = "";
            for (let i = 0; i < rows.length; i++)
                merged += (i > 0 ? "\n" : "") + rows[i].text;

            source.diffRows = rows;
            source.showAgentEdit(merged);
        }
    }

    // Take the turn: drop the old lines, keep the new ones, and run. The undo
    // stays armed — the reason to take an edit back is nearly always the
    // picture, and the picture is only there once it has run.
    function acceptAgentEdit() {
        const kept = Agent.accepted();
        Agent.accept();
        source.diffRows = [];
        source.showAgentEdit(kept);
        app.executeScene(true);
    }

    // Drop it, whether or not it was taken. Nothing is run: the file goes back
    // to what it was, and what was on screen was already that.
    function undoAgentEdit() {
        if (!Agent.revertable())
            return false;
        const back = Shell.readTextFile(source.path);
        Agent.revert();
        source.diffRows = [];
        source.showAgentEdit(Shell.readTextFile(source.path));
        if (app.execState !== "none")
            app.executeScene(false);
        return true;
    }

    Shortcut {
        sequence: Keymap.sequence("execute")
        onActivated: {
            if (Agent.pending)
                app.acceptAgentEdit();
            else
                app.executeScene(true);
        }
    }

    // ⌘Z is the editor's own undo, except while an agent turn is still the last
    // thing that happened — then it takes the WHOLE turn back in one press,
    // which is the unit the turn was asked for in. `Agent.disarm()` hands the
    // key back the moment the author types anything of their own.
    Shortcut {
        // `sequences`, not `sequence`: undo is spelled more than one way on this
        // platform, and binding the single form takes only the first of them.
        sequences: [StandardKey.Undo]
        enabled: Agent.revertable
        onActivated: app.undoAgentEdit()
    }

    // Play, pause, or start over.
    //
    // The playhead parks at the end when a scene finishes, so the next Space
    // asked the clock to advance past the end and it stopped again on the same
    // frame: play appeared to do nothing at all. Pressing play on a finished
    // scene means "again" — every player on this machine agrees — so it rewinds
    // first. Pausing mid-scene still leaves the playhead where you stopped it.
    function togglePlay() {
        if (!playing) {
            // Where "again" starts. With a range set that is its in point, and
            // pressing play anywhere outside the range means you want the range
            // — you marked it a moment ago for exactly this.
            const from = ranged ? markIn : 0;
            const until = ranged ? markOut : shownScene.duration;
            // One frame of slack, because the last FRAME sits at `until - 1/fps`
            // and not at `until`. Testing against `until` alone left a playhead
            // parked on the last frame looking unfinished: play advanced one
            // tick, hit the end, and stopped again on the frame it started on.
            const spent = until - 1 / execFps + 1e-6;
            if (playhead >= spent || playhead < from - 1e-6)
                playhead = from;
        }
        playing = !playing;
    }

    // Playback advances the playhead one frame per tick, and the preview
    // renders whatever frame it lands on. A frame clock rather than a wall
    // clock: rendering happens on demand on this thread, so chasing real time
    // would mean claiming a frame rate the pane is not delivering.
    Timer {
        id: clock
        interval: Math.max(1, Math.round(1000 / app.execFps))
        repeat: true
        running: app.playing && app.shownScene.duration > 0
        onTriggered: {
            const next = app.playhead + 1 / app.execFps;
            const until = app.ranged ? app.markOut : app.shownScene.duration;
            if (next >= until) {
                app.playhead = until;
                app.playing = false;
            } else {
                app.playhead = next;
            }
        }
    }

    Timer {
        id: colouring
        interval: 400
        onTriggered: if (source.path.length > 0) Lsp.semanticTokens(source.path)
    }

    // A rebinding is a setting, so it is written where every other setting is.
    Connections {
        target: Keymap
        function onChanged() { app.saveLayout(); }
    }

    DockDialog {
        id: confirmReset
        anchors.fill: parent
        z: 300
        title: "Reset " + app.templateLabel(app.template) + "?"
        // What it lands on, said out loud. "How it ships" and "the shape you
        // pinned with Update default" are very different answers, and the one
        // you get depends on something you may have done weeks ago — so the
        // dialog reads the answer rather than describing the rule.
        message: (app.defaults[app.template] !== undefined
                  ? "It goes back to the shape you pinned with Update default, and the changes you have made since are forgotten. "
                  : "You have never pinned a default for this one, so it goes back to how it SHIPS — not to the shape you have been working in. ")
                 + "Save it under a name first if you want it back later."
        extraLabel: "Save it first…"
        acceptLabel: "Reset"
        destructive: true
        onAccepted: app.resetLayout()
        onExtraChosen: saveDisplay.ask()
    }

    DockDialog {
        id: saveDisplay
        anchors.fill: parent
        z: 300
        title: "Save this display"
        message: "It joins Load display, and comes back exactly as it is now — "
                 + "panes, sizes, floating windows and all."
        asksName: true
        placeholder: app.templateLabel(app.template) + " (mine)"
        acceptLabel: "Save"
        onAccepted: (name) => app.saveDisplay(name)
    }

    DockMenu {
        id: menu
        anchors.fill: parent
        z: 100
        onChosen: (entry) => app.runMenu(entry)
    }

    // ── Panels torn out of the dock ───────────────────────────────────────
    // A Repeater only makes Items and a window is not one, so the floating
    // panels are instantiated rather than repeated.
    Instantiator {
        model: app.floats

        delegate: Window {
            id: floater
            required property var modelData

            width: floater.modelData.w
            height: floater.modelData.h
            x: floater.modelData.x
            y: floater.modelData.y
            visible: true
            color: Theme.ground
            title: app.panelTitles[floater.modelData.keys[floater.modelData.current]] + " — video-code"

            Panel {
                anchors.fill: parent
                anchors.margins: Theme.gap
                slotId: floater.modelData.id
                keys: floater.modelData.keys
                current: floater.modelData.current
                titles: app.panelTitles
                items: app.panelItems
                dropZone: app.hoverSlot === floater.modelData.id ? app.hoverZone : ""

                Component.onCompleted: app.registerNode(floater.modelData.id, this)
                Component.onDestruction: app.forgetNode(floater.modelData.id, this)

                onFloatRequested: {} // already a window of its own
                onTabPicked: (index) => app.pickTab(floater.modelData.id, index)
                onTabClosed: (key) => app.closeTab(floater.modelData.id, key)
                onMenuRequested: (x, y) => app.openMenu(floater.modelData.id, x, y)
                onTabDragMoved: (x, y) => app.dragOver(floater.modelData.id, x, y)
                onTabDropped: (key, x, y) => app.drop(floater.modelData.id, key, x, y)
            }

            // Closing the window puts the panel away, exactly as closing its tab
            // would: one panel, one meaning for "close".
            onClosing: {
                const keys = floater.modelData.keys.slice();
                for (let i = 0; i < keys.length; i++)
                    app.closeTab(floater.modelData.id, keys[i]);
            }
        }
    }

    // ── The panels themselves, created once and reparented by the slots ────
    // Keeping them out of the dock's own tree is what makes moving one free: the
    // buffer, the selection and the scroll positions all survive the trip.
    PreviewPanel {
        id: preview
        visible: false
        playhead: app.playhead
        playing: app.playing
        framerate: app.execFps
        revision: app.execRevision
        ready: app.execRevision > 0
        onTogglePlay: app.togglePlay()
        onSeek: (seconds) => app.playhead = Math.max(0, Math.min(seconds, app.shownScene.duration))
    }

    TimelinePanel {
        id: timeline
        visible: false
        scene: app.shownScene
        // Which bar is out of its lane, so the lane can be drawn hollow for
        // exactly as long as the flight and the card last.
        openedName: elementCard.element !== null && elementCard.element.n !== undefined
                    ? elementCard.element.n : ""
        onElementOpened: (element, where) => elementCard.open(element, where)
        // Scrubbing stops playback: the two are the same control, and a playhead
        // that keeps running away from where you put it is not a scrub.
        // A gap edited on the timeline is one number rewritten in the file: the
        // wait carries the line it was written on, and `wait(0.3)` writes its
        // seconds without a name, so the span comes from the positional writer.
        onTrimmed: (element, edge, seconds) => app.trimElement(element, edge, seconds)
        onWaitChanged: (line, seconds) => {
            const value = parseFloat(seconds);
            if (isNaN(value) || value < 0) {
                source.say("a gap is a number of seconds");
                return;
            }

            const span = Shell.positionalSpan(source.text, line, "wait", 0, value.toString());
            if (!span.ok) {
                source.say("could not write that wait");
                return;
            }

            source.replaceRange(span.start, span.end, span.text);
            app.executeScene();
        }

        onScrubbed: (seconds) => {
            app.playing = false;
            app.playhead = Math.max(0, Math.min(seconds, app.shownScene.duration));
        }
        selectedIndex: app.selectedIndex
        playhead: app.playhead
        markIn: app.markIn
        markOut: app.markOut
        snapPoints: app.snapPoints
        onElementPicked: (index) => app.selectedIndex = index
    }

    AgentPanel {
        id: agent
        visible: false
    }

    // The scene, edited here and understood by a language server of our own.
    //
    // This pane used to host the real VS Code, over `code serve-web` in a
    // WKWebView. It worked, and it cost 9 % CPU at rest for intelligence that
    // is not VS Code's to begin with: definitions, hovers, signatures,
    // completion, diagnostics, references and rename all come from LSP, which
    // pyright speaks standing alone. What was lost with it — the extension
    // marketplace — was never what this pane was for. See docs/ui/CODE-PANE.md.
    SourcePanel {
        id: source
        visible: false
        name: "scene"
        onDocumentReady: (document) => Shell.highlightPython(document, Theme.code)
        onExecuteRequested: app.executeScene(true)

        onSaveRequested: {
            if (source.path.length === 0)
                return;
            if (source.readOnly) {
                source.say("read-only — outside the project");
                return;
            }
            if (!Shell.writeTextFile(source.path, source.text)) {
                source.say("could not write " + source.name);
                return;
            }
            source.modified = false;

            // Saving IS an execute, like opening one.
            //
            // ⌘R exists because the timeline must not flicker under your typing:
            // between two keystrokes a scene is half-written, and running it
            // thirty times a second would be thirty answers to a question you
            // have not finished asking. A save is the opposite — it is you saying
            // the edit is done — and a preview still showing what the file no
            // longer says is the one lie a preview must not tell.
            //
            // Nothing is rendered here that would not be rendered anyway: the
            // scene is re-run (single-digit milliseconds) and the pane redraws
            // the one frame the playhead is on.
            app.executeScene();
            source.say(app.execState === "fresh"
                       ? "saved · ran in " + app.execMs.toFixed(0) + " ms"
                       : "saved");
        }
        // Compared against what was last SENT, not merely non-empty: repainting
        // the buffer changes its formats, Qt reports that as a text change, and
        // taking it at face value made the pane tell the server about an edit
        // that had not happened — which came back as new tokens, which repainted
        // the buffer, for ever.
        // The spans belong to the file that just left. The highlighter keeps
        // them until told otherwise, and it holds LINE and COLUMN — so they
        // land on whatever text is now at those coordinates: opening eg.py
        // after scene.py painted `ocode ` teal, because scene.py had a class
        // at line 4 column 9. Cleared here, and asked for again.
        onOpened: (where, body) => {
            app.sentText = body;
            if (source.document !== null)
                Shell.applySemanticTokens(source.document, []);
            colouring.restart();
        }

        onTextChanged: {
            if (source.loading || source.path.length === 0 || source.text === app.sentText)
                return;
            app.sentText = source.text;
            // The server is told at once — completion, hovers and signatures all
            // answer about the text as it is now, and a stale document would
            // make them lie. What waits is the REPORTING of what it finds on the
            // line under your hands; see SourcePanel.shownDiagnostics.
            Lsp.changeDocument(source.path, source.text);
            source.noteEdit();
            colouring.restart();
        }
    }

    LibraryPanel {
        id: library
        visible: false
        catalogue: app.placeable
        onCarrying: (template, values, x, y) => app.carryTemplate(template, values, x, y)
        onDropped: (template, values, x, y) => app.dropTemplate(template, values, x, y)
        onReleased: app.carried = null
    }

    MediaPanel {
        id: media
        visible: false
        sceneAssets: app.sceneAssets
        scene: app.shownScene
        added: app.addedAssets
        display: app.mediaDisplay
        onAddRequested: app.addMedia()
        onAssetCarried: (asset, x, y) => app.carryAsset(asset, x, y)
        onAssetDropped: (asset, x, y) => app.dropAsset(asset, x, y)
        onCarryCancelled: app.carried = null
    }

    // ── Keys ──────────────────────────────────────────────────────────────
    // The transport keys the preview window already answers to, kept identical
    // so the two windows are not two different applications.
    // Read from Keymap rather than spelled here, so they appear on the keyboard
    // board and can be rebound like everything else. They were the one set of
    // keys the board could not see — which made its claim to be the whole truth
    // false by exactly five lines.
    // ── Transport, and the caret ──────────────────────────────────────────
    // All five are keys a text editor already owns. While the caret is in the
    // code pane they stay the editor's — Space writes a space, the arrows move
    // the caret — and the transport gets them back the moment you click on the
    // picture or the timeline.
    //
    // The alternative was a Shortcut that wins over the pane, and it is worse
    // than it sounds: `TextEdit` claims the key through ShortcutOverride, so the
    // shortcut never fires AND the space still lands in the buffer. Nothing
    // played, and the scene quietly went stale.
    Shortcut {
        sequence: Keymap.sequence("play")
        enabled: !source.typing
        onActivated: app.togglePlay()
    }
    Shortcut {
        sequence: Keymap.sequence("toStart")
        enabled: !source.typing
        onActivated: app.playhead = 0
    }
    Shortcut {
        sequence: Keymap.sequence("toEnd")
        enabled: !source.typing
        onActivated: app.playhead = app.shownScene.duration
    }
    Shortcut {
        sequence: Keymap.sequence("prevFrame")
        enabled: !source.typing
        onActivated: app.playhead = Math.max(0, app.playhead - 1 / preview.framerate)
    }
    Shortcut {
        sequence: Keymap.sequence("nextFrame")
        enabled: !source.typing
        onActivated: app.playhead = Math.min(app.shownScene.duration, app.playhead + 1 / preview.framerate)
    }
    // The range. `I` and `O` are the two keys every editor on this machine
    // spells the same way, and the third gives the whole scene back.
    Shortcut {
        sequence: Keymap.sequence("markIn")
        enabled: !source.typing
        onActivated: app.setMarkIn()
    }
    Shortcut {
        sequence: Keymap.sequence("markOut")
        enabled: !source.typing
        onActivated: app.setMarkOut()
    }
    Shortcut {
        sequence: Keymap.sequence("clearMarks")
        enabled: !source.typing
        onActivated: app.clearMarks()
    }
    Shortcut {
        sequence: "Escape"
        onActivated: {
            // Escape puts away what is on top before it touches the selection.
            if (confirmReset.visible)
                confirmReset.close();
            else if (saveDisplay.visible)
                saveDisplay.close();
            else if (menu.visible)
                menu.visible = false;
            else if (app.measuring)
                app.measuring = false;
            else if (elementCard.element !== null)
                // The card answers Escape itself while it holds the keyboard —
                // its own ladder has more rungs than this one. But typing in a
                // parameter field leaves the focus inside the card and this
                // shortcut wins, and Escape has to mean the same thing either
                // way: put away what is on top.
                elementCard.dismiss();
            else
                app.selectedIndex = -1;
        }
    }
}
