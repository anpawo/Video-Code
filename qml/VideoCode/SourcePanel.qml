// The scene's source, and everything the editor knows about it.
//
// The buffer is the scene: gestures on the timeline rewrite it, and it reaches
// the filesystem when you save. What makes this an editor rather than a text box
// is the language server behind it — diagnostics, hovers, completion,
// signatures, definitions, references and rename all come from LSP, and each one
// is a few lines here because the protocol does the thinking.
pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls

Item {
    id: root

    property alias text: editor.text

    // What an agent turn changed, as `{kind, text}` rows in file order —
    // "same", "add" or "del". Empty when nothing is pending.
    //
    // The diff is shown HERE and not in the agent pane on purpose: what an edit
    // did to a scene is a fact about this file, and reading it anywhere else
    // means holding two places in your head at once. The buffer carries the
    // merged view while it is pending — the old lines and the new ones — so the
    // text on screen is briefly not valid Python. That is why the analyser is
    // told to hold: see `diffPending`.
    property var diffRows: []
    readonly property bool diffPending: diffRows.length > 0
    property string name: "untitled.py"
    // Whether the buffer differs from what is on disk. Shown by the pane's tab,
    // which is the only place left that can show it now that the pane has no
    // strip of its own.
    property bool modified: false

    signal saveRequested()

    // Run the scene. Handled here as well as by the window's Shortcut, because
    // this is where the key is actually pressed — and because a Qt Shortcut is
    // matched by the platform's key handler, so a synthetic event never reaches
    // it and the whole path would be untestable.
    signal executeRequested()

    // The buffer's document, offered once it exists. The panel does not know
    // what a syntax highlighter is or that a C++ shell exists — it says "here is
    // the document" and the shell decides what to do about it.
    signal documentReady(var document)

    // The document the buffer is painted through, kept so the shell can hand it
    // the analyser's tokens when they arrive.
    property var document: null

    // Whether this file can be written at all. A file outside the project is
    // shown but never saved — following a definition into a library is reading,
    // not editing, and the pane says so rather than swallowing the ⌘S.
    readonly property bool readOnly: root.path.length > 0 && !Shell.writable(root.path)

    // True while a file is being swapped in. Every edit the pane reports during
    // that moment is the swap itself, not something a person typed.
    property bool loading: false

    // A file has been swapped in, and this is what it holds.
    signal opened(string where, string body)

    // ── What the language server found ────────────────────────────────────
    // Raw LSP diagnostics: { range: { start/end: { line, character } },
    // severity, message, source }. Kept in the protocol's shape rather than
    // translated, so that adding a field never means touching a converter.
    property var diagnostics: []

    // What the RUN said — the warnings `execSource` collects, and the failure
    // when a scene does not run at all. Kept in a list of its own because the
    // analyser publishes a WHOLE list on every pause in typing: anything written
    // into `diagnostics` beside it is erased a second later, which is how the
    // run's warnings were drawn and then quietly dropped before anyone read one.
    property var runFlaws: []

    // ── Not while you are still writing it ────────────────────────────────
    // A half-typed line is not a mistake, and being told it is one is noise you
    // learn to ignore — which is how a real error later goes unread.
    //
    // The analyser already waits: pyright backs off 250 ms from the last thing
    // you did and re-arms that on every keystroke, so it never runs mid-word.
    // What it cannot know is WHERE your hands are. It answers about the whole
    // file, and the answer arrives the moment you pause — including about the
    // line you are in the middle of.
    //
    // So the pane holds back only that line, and only while you are typing:
    // everything else in the file is reported as it always was, and the line you
    // are on joins them once you have been still for `settleDelay`.
    readonly property int settleDelay: 600
    property bool settling: false
    property int writingLine: -1

    function noteEdit() {
        root.settling = true;
        root.writingLine = root.locationAt(editor.cursorPosition).line;
        settle.restart();
    }

    Timer {
        id: settle
        interval: root.settleDelay
        onTriggered: {
            root.settling = false;
            root.writingLine = -1;
        }
    }

    // What is actually shown: everything, minus what is being written.
    readonly property var shownDiagnostics: {
        const all = root.diagnostics.concat(root.runFlaws);
        if (!root.settling || root.writingLine < 0)
            return all;
        return all.filter((d) => d.range.start.line !== root.writingLine);
    }

    // One size for everything that shows code or sits beside it. VS Code's
    // hovers and lists are drawn at the editor's own size, and the difference
    // shows: a signature a step smaller than the line it explains reads as a
    // footnote rather than as the answer.
    readonly property int codeSize: editor.font.pixelSize

    // The buffer's file on disk. The language server reasons about paths, so a
    // pane with no path simply has no intelligence — everything below degrades
    // to a plain editor rather than breaking.
    property string path: ""

    // ── Where you have been ───────────────────────────────────────────────
    // Following a definition into another file is only useful if coming back is
    // free. Two stacks, the browser's model, because it is the one everybody
    // already has in their fingers — and ⌘← / ⌘→ are the keys they press.
    property var back: []
    property var forward: []

    // Opening a file the pane was not showing. The buffer is told to the server
    // as it opens, because a file nobody has opened has no diagnostics and
    // answers no questions about itself.
    // Put text in the buffer that did NOT come from a person: an agent's edit,
    // or the file being put back after one. Goes through the same gate as
    // `load` — `ready` off — so it is not counted as a modification and does
    // not wake the analyser on a buffer that may be holding both sides of a
    // diff.
    function showAgentEdit(body) {
        editor.ready = false;
        editor.text = body;
        editor.pristine = body;
        root.modified = false;
        editor.ready = true;
        // The server is told only about text that is really the file. While a
        // diff is pending the buffer is a merged view, and telling pyright about
        // it would answer with errors about lines nobody wrote.
        if (!root.diffPending && root.path.length > 0)
            Lsp.changeDocument(root.path, body);
    }

    function load(where, line, character) {
        if (where !== root.path) {
            const body = Shell.readTextFile(where);

            // The PATH is set before the text, and the shell is told to hold
            // its sync while both move.
            //
            // Assigning the text first fires the change signal while `path`
            // still names the file being left — so the shell dutifully told the
            // server that scene.py now contained Rectangle.py, and coming back
            // told it the opposite. One jump and back left the analyser holding
            // two files' contents under each other's names, which is why the
            // return landed on sixty diagnostics that were not there before.
            root.loading = true;
            editor.ready = false;
            root.path = where;
            editor.text = body;
            editor.pristine = body;
            root.name = where.split("/").pop();
            root.modified = false;
            root.diagnostics = [];
            editor.ready = true;
            root.loading = false;

            // The one true statement about this file, made once and by hand.
            Lsp.openDocument(where, body);
            root.opened(where, body);
        }
        if (line !== undefined) {
            editor.cursorPosition = root.offsetOf(line, character !== undefined ? character : 0);
            // The line asked for, shown a third of the way down rather than at
            // the very bottom edge where a jump usually lands it.
            (view.contentItem as Flickable).contentY =
                Math.max(0, editor.cursorRectangle.y - view.height / 3);
        }
        // Only a pane you can see takes the caret. Following a definition is a
        // request to type; the scene loaded at startup, into a pane that is not
        // even in the dock yet, is not — and taking the keyboard there is how
        // Space stopped playing.
        if (root.visible)
            editor.forceActiveFocus();
    }

    // A jump is a load that remembers what it left, and forgets the way
    // forward — same as clicking a link after going back.
    function jump(where, line, character) {
        if (root.path.length > 0)
            root.back = root.back.concat([{ path: root.path, offset: editor.cursorPosition }]);
        root.forward = [];
        root.load(where, line, character);
    }

    function goBack() {
        if (root.back.length === 0)
            return;
        const mark = root.back[root.back.length - 1];
        root.back = root.back.slice(0, -1);
        root.forward = root.forward.concat([{ path: root.path, offset: editor.cursorPosition }]);
        root.load(mark.path);
        editor.cursorPosition = Math.min(mark.offset, editor.text.length);
    }

    function goForward() {
        if (root.forward.length === 0)
            return;
        const mark = root.forward[root.forward.length - 1];
        root.forward = root.forward.slice(0, -1);
        root.back = root.back.concat([{ path: root.path, offset: editor.cursorPosition }]);
        root.load(mark.path);
        editor.cursorPosition = Math.min(mark.offset, editor.text.length);
    }

    // A list from the server arrives as a JS-array-LIKE object, not a JS array:
    // Array.isArray() is false for it, which silently turned every reply into
    // "not a list" and made go-to-definition do nothing at all. Length is the
    // honest test on this side of the bridge.
    function listed(reply) {
        if (reply === undefined || reply === null)
            return [];
        if (typeof reply === "string")
            return [reply];
        return reply.length !== undefined ? reply : [reply];
    }

    // A definition reply is one location, a list of them, or a link with the
    // target range spelled differently. All three name a file and a line.
    function follow(reply) {
        const first = root.listed(reply)[0];
        if (!first)
            return;
        const where = first.uri !== undefined ? first.uri : first.targetUri;
        const range = first.range !== undefined ? first.range : first.targetSelectionRange;
        if (where === undefined || range === undefined)
            return;
        root.jump(where.replace("file://", ""), range.start.line, range.start.character);
    }

    // ── Renaming, everywhere at once ──────────────────────────────────────
    // The server answers with a WorkspaceEdit: every file that mentions the
    // name, and where in it. Most of those files are not open — a rename that
    // only fixed the visible buffer would leave the project broken, so the
    // edits go to disk.
    //
    // Edits are applied from the END of each file backwards, because applying
    // one from the top moves every offset below it.
    function applyEdit(edit) {
        if (!edit)
            return 0;

        // Two spellings of the same thing, both legal.
        let byFile = ({});
        if (edit.changes !== undefined) {
            for (const uri in edit.changes)
                byFile[uri.replace("file://", "")] = root.listed(edit.changes[uri]);
        }
        for (const change of root.listed(edit.documentChanges)) {
            if (change.textDocument === undefined)
                continue;
            byFile[change.textDocument.uri.replace("file://", "")] = root.listed(change.edits);
        }

        let touched = 0;
        for (const where in byFile) {
            const open = where === root.path;
            let body = open ? editor.text : Shell.readTextFile(where);
            if (body.length === 0 && !open)
                continue;

            let edits = [];
            for (const one of byFile[where])
                edits.push(one);
            edits.sort(function (a, b) {
                return b.range.start.line - a.range.start.line
                    || b.range.start.character - a.range.start.character;
            });

            const lines = body.split("\n");
            for (const one of edits) {
                const line = lines[one.range.start.line];
                if (line === undefined)
                    continue;
                // Single-line edits only: renaming a symbol never spans lines,
                // and pretending to handle what cannot happen hides the day it
                // does behind a silently wrong buffer.
                if (one.range.end.line !== one.range.start.line)
                    continue;
                lines[one.range.start.line] = line.substring(0, one.range.start.character)
                                            + one.newText
                                            + line.substring(one.range.end.character);
            }

            const next = lines.join("\n");
            if (open) {
                const caret = editor.cursorPosition;
                editor.text = next;
                editor.cursorPosition = Math.min(caret, next.length);
            } else if (!Shell.writeTextFile(where, next)) {
                continue;
            }
            ++touched;
        }
        return touched;
    }

    // A line/character pair is where the protocol counts; a character offset is
    // where a TextArea counts. One walk of the buffer converts between them.
    function offsetOf(line, character) {
        const lines = editor.text.split("\n");
        let offset = 0;
        for (let i = 0; i < line && i < lines.length; ++i)
            offset += lines[i].length + 1;
        return offset + Math.min(character, line < lines.length ? lines[line].length : 0);
    }

    // The other direction: where the mouse is, told in the protocol's terms.
    function locationAt(offset) {
        const before = editor.text.substring(0, offset).split("\n");
        return { line: before.length - 1, character: before[before.length - 1].length };
    }

    // A hover reply is markdown, or a plain string, or a list of either — three
    // shapes the protocol allows and every server picks from differently. What
    // the pane wants is text, so all three collapse to one here, and the code
    // fences go: the bubble is monospaced already, and ``` on its own line is
    // noise the reader has to look past.
    function readable(reply) {
        if (!reply || !reply.contents)
            return { code: "", prose: "" };
        const parts = root.listed(reply.contents);
        let out = [];
        for (const part of parts)
            out.push(typeof part === "string" ? part : (part.value !== undefined ? part.value : ""));
        const whole = out.join("\n");

        // The fenced block is the SIGNATURE and everything else is the
        // docstring. Kept apart because they are read differently: one is code
        // and gets coloured like code, the other is a sentence.
        let code = "";
        let prose = whole;
        const fenced = /```[a-z]*\n([\s\S]*?)```/.exec(whole);
        if (fenced !== null) {
            code = fenced[1].trim();
            prose = whole.replace(fenced[0], "");
        }

        return { code: code, prose: root.unmarked(prose) };
    }

    // Markdown, undone. A docstring arrives escaped for a renderer we do not
    // have, and the escapes show through as themselves: `&nbsp;` in the middle
    // of an example, `\[` around a list, `&lt;` where someone wrote `<`. Reading
    // those is worse than reading no documentation at all.
    function unmarked(text) {
        return text
            .replace(/```[a-z]*\n?/g, "")
            .replace(/&nbsp;/g, " ")
            .replace(/&lt;/g, "<")
            .replace(/&gt;/g, ">")
            .replace(/&amp;/g, "&")
            .replace(/\\([\[\]()*_#`~-])/g, "$1")
            .replace(/^\s*-{3,}\s*$/gm, "")
            .replace(/\n{3,}/g, "\n\n")
            .trim();
    }

    // The word being typed, which is both what the list filters on and what an
    // accepted completion replaces. Anything a Python identifier can hold.
    function wordStart() {
        let at = editor.cursorPosition;
        while (at > 0 && /[A-Za-z0-9_]/.test(editor.text.charAt(at - 1)))
            --at;
        return at;
    }

    // The protocol's kinds, as the one letter that fits beside a name. Only the
    // ones Python actually produces are named; the rest fall back to a dot,
    // which says "something" without pretending to know what.
    function kindMark(kind) {
        const marks = {
            2: "m", 3: "f", 4: "f", 5: "p", 6: "v", 7: "C", 8: "I",
            9: "M", 10: "p", 14: "k", 21: "c", 22: "S"
        };
        return marks[kind] !== undefined ? marks[kind] : "·";
    }

    function kindColor(kind) {
        if (kind === 7 || kind === 8 || kind === 22) return Theme.ai;      // types
        if (kind === 2 || kind === 3 || kind === 4) return Theme.ok;       // callables
        if (kind === 14) return Theme.live;                               // keywords
        return Theme.inkDim;
    }

    function severityColor(severity) {
        if (severity === 1) return Theme.bad;
        if (severity === 2) return Theme.flaw;
        return Theme.ai;
    }

    // ── Which file this is ────────────────────────────────────────────────
    // Under the tabs rather than in them: a tab is a place in the dock, and the
    // dock's tabs are named after what they DO. Following a definition lands you
    // in another file, and the pane has to say which one without renaming the
    // place you are in.
    Rectangle {
        id: filebar
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: 20
        color: Theme.codeSkin.ground

        Text {
            anchors {
                left: parent.left; leftMargin: 10
                right: state.left; rightMargin: 8
                verticalCenter: parent.verticalCenter
            }
            // Relative to the project when it is inside it: the full path of a
            // file three folders down is mostly the same prefix as every other.
            text: root.path.indexOf(Shell.projectRoot() + "/") === 0
                  ? root.path.substring(Shell.projectRoot().length + 1)
                  : root.path
            color: Theme.codeSkin.line
            font.family: Theme.mono
            font.pixelSize: root.codeSize - 2
            elide: Text.ElideLeft
        }

        Text {
            id: state
            anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
            text: root.readOnly ? "read-only" : (root.modified ? "•" : "")
            color: root.readOnly ? Theme.warn : Theme.codeSkin.ink
            font.family: Theme.mono
            font.pixelSize: root.codeSize - 2
        }

        Rectangle {
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            height: 1
            color: Theme.edgeSoft
        }
    }

    // The sunken surface is the whole editing area, not just the lines that
    // happen to be typed — a TextArea's own background stops at the last line,
    // which left the bottom of the panel a different colour and its corners
    // square. Drawn once here, it carries the panel's bottom corners too.
    Rectangle {
        anchors {
            left: parent.left; right: parent.right
            top: filebar.bottom; bottom: parent.bottom
        }
        color: Theme.codeSkin.ground
        bottomLeftRadius: Theme.radiusInner
        bottomRightRadius: Theme.radiusInner
    }

    // ── The gutter ────────────────────────────────────────────────────────
    // Line numbers are not decoration in this editor: a traceback from the
    // compiled scene points at a line, and a gesture on the timeline rewrites
    // one. Without numbers, neither can be pointed at out loud.
    //
    // It scrolls by following the view rather than living inside it, because a
    // gutter that scrolls sideways with the text stops being a gutter the moment
    // a line is longer than the pane.
    Rectangle {
        id: gutter
        anchors {
            left: parent.left
            top: filebar.bottom; bottom: parent.bottom
        }
        // As wide as the widest number it will ever draw, and no wider. A fixed
        // 44 px was two characters of air on a sixteen-line scene and too tight
        // the day a file passes a thousand lines — measured from the font rather
        // than guessed, so it holds at any size.
        width: digits.width + 18
        color: Theme.codeSkin.ground
        clip: true

        TextMetrics {
            id: digits
            font: editor.font
            text: "0".repeat(Math.max(String(editor.lineCount).length, 2))
        }

        readonly property real lineHeight: editor.lineCount > 0
                                           ? editor.contentHeight / editor.lineCount : 16

        Column {
            // A ScrollView's contentItem IS the Flickable it scrolls with; the
            // cast is what lets the binding — and qmllint — see contentY.
            y: editor.topPadding - (view.contentItem as Flickable).contentY

            Repeater {
                model: editor.lineCount

                Text {
                    id: number
                    required property int index
                    width: gutter.width - 10
                    height: gutter.lineHeight
                    horizontalAlignment: Text.AlignRight
                    verticalAlignment: Text.AlignVCenter
                    // A touched line says so in the margin as well as behind the
                    // text: a diff read at a glance is read down the gutter.
                    readonly property string mark: number.index < root.diffRows.length
                                                   ? root.diffRows[number.index].kind : "same"
                    text: number.mark === "add" ? "+" : number.mark === "del" ? "−" : number.index + 1
                    color: number.mark === "add" ? Theme.ok
                           : number.mark === "del" ? Theme.bad
                           : number.index === editor.currentLine ? Theme.codeSkin.ink : Theme.codeSkin.line
                    font.family: Theme.mono
                    font.pixelSize: root.codeSize - 1
                }
            }
        }

        // The same news as the squiggle, at the one place you can see the whole
        // file from: a file with an error two screens down looks clean without
        // this, and you only find out when you run it.
        Repeater {
            model: root.shownDiagnostics

            Rectangle {
                id: mark
                required property var modelData
                x: 4
                y: editor.topPadding - (view.contentItem as Flickable).contentY
                   + mark.modelData.range.start.line * gutter.lineHeight
                   + (gutter.lineHeight - height) / 2
                width: 5
                height: 5
                radius: 2.5
                color: root.severityColor(mark.modelData.severity)
            }
        }

        Rectangle {
            anchors { right: parent.right; top: parent.top; bottom: parent.bottom }
            width: 1
            color: Theme.edgeSoft
        }
    }

    // ── The bubble ────────────────────────────────────────────────────────
    // A child of the panel rather than of the text, so that a signature found on
    // the last visible line is not clipped away by the scroll view — it is
    // allowed to cover the code, which is what every editor does and what makes
    // it readable.
    Rectangle {
        id: tip
        visible: false
        z: 10
        width: Math.min(Math.max(signature.implicitWidth, body.implicitWidth) + 18, root.width - 24)
        height: bubble.implicitHeight + 16
        // The bubble belongs to the CODE, not to the chrome: VS Code paints its
        // hovers on their own surface, a step up from the editor's ground, and a
        // panel-blue box over a black buffer reads as a different application.
        color: Theme.codeSkin.hover
        radius: Theme.radiusSmall
        border.width: 1
        border.color: Theme.codeSkin.edge

        function show(what, cx, cy) {
            if (what.code.length === 0 && what.prose.length === 0) {
                tip.visible = false;
                return;
            }
            signature.text = what.code;
            body.text = what.prose;
            const at = editor.mapToItem(root, cx, cy);
            // Kept inside the pane on both axes: a bubble half off the right
            // edge is worse than one that does not line up with the word.
            tip.x = Math.max(8, Math.min(at.x, root.width - tip.width - 8));
            tip.y = at.y + tip.height + 6 > root.height ? at.y - tip.height - 18 : at.y + 6;
            tip.visible = true;
        }

        function hide() { tip.visible = false; }

        Column {
            id: bubble
            anchors.fill: parent
            anchors.margins: 8
            spacing: signature.text.length > 0 && body.text.length > 0 ? 7 : 0

            // A TextEdit rather than a Text, for one reason: it owns a document,
            // and a document is what a syntax highlighter attaches to. The
            // signature is code, so it is painted by the same rules and the same
            // palette as the buffer behind it.
            TextEdit {
                id: signature
                width: bubble.width
                visible: text.length > 0
                readOnly: true
                selectByMouse: false
                color: Theme.codeSkin.ink
                font.family: Theme.mono
                font.pixelSize: root.codeSize
                wrapMode: TextEdit.NoWrap
                textFormat: TextEdit.PlainText

                Component.onCompleted: root.documentReady(signature.textDocument)

                Connections {
                    target: Theme
                    function onCodeThemeChanged() { root.documentReady(signature.textDocument); }
                }
            }

            Rectangle {
                width: bubble.width
                height: 1
                visible: signature.text.length > 0 && body.text.length > 0
                color: Theme.edgeSoft
            }

            Text {
                id: body
                width: bubble.width
                visible: text.length > 0
                color: Theme.codeSkin.ink
                font.family: Theme.ui
                font.pixelSize: root.codeSize
                wrapMode: Text.Wrap
                textFormat: Text.PlainText
            }
        }
    }

    // A whole statement, put in on its own line above the caret's.
    //
    // Above rather than at the caret: a dropped file lands while you are in the
    // middle of a line as often as not, and splitting `Square(sid` in half is a
    // worse answer than a line you can move.
    function insertLine(statement) {
        // Nobody has placed the caret yet — position 0 is where it starts — so
        // "add this to my scene" means the end, not above the shebang. Once the
        // caret has been somewhere, that somewhere is the answer.
        if (editor.cursorPosition === 0) {
            const tail = editor.text.endsWith("\n") ? "" : "\n";
            editor.insert(editor.text.length, tail + statement + "\n");
            editor.cursorPosition = editor.text.length - 1;
            editor.forceActiveFocus();
            return;
        }

        const at = editor.text.lastIndexOf("\n", Math.max(0, editor.cursorPosition - 1)) + 1;
        editor.insert(at, statement + "\n");
        editor.cursorPosition = at + statement.length;
        editor.forceActiveFocus();
    }

    // A statement placed under a line the gesture chose, rather than under the
    // caret. Trimming a shape writes `square.hide(start=…)`, and WHERE that
    // lands decides what it means: `start` is counted from the element's cursor,
    // and the cursor is only what it was on the line the editor measured.
    //
    // Through `replaceRange` so the insertion is one entry in the same undo
    // history as typing — and it takes the indentation of the line it follows,
    // because a statement written flush left inside a function is a syntax
    // error rather than an edit.
    function insertAfterLine(line, statement) {
        const lines = editor.text.split("\n");
        if (line < 1 || line > lines.length)
            return false;

        let offset = 0;
        for (let i = 0; i < line; ++i)
            offset += lines[i].length + 1;

        const indent = /^\s*/.exec(lines[line - 1])[0];
        return root.replaceRange(offset, offset, indent + statement + "\n");
    }

    // Several statements at once, as ONE edit: a template is a line that makes
    // the thing and a line that says when it appears, and two insertions would
    // be two ⌘Z. Blank line in front when there is not one already, because a
    // block that starts flush against the line above reads as part of it.
    function insertBlock(afterLine, statements) {
        const lines = editor.text.split("\n");
        if (afterLine < 0 || afterLine > lines.length)
            return false;

        let offset = 0;
        for (let i = 0; i < afterLine; ++i)
            offset += lines[i].length + 1;

        const indent = afterLine > 0 ? /^\s*/.exec(lines[afterLine - 1])[0] : "";
        // A blank line on whichever side does not already have one, so the block
        // reads as its own paragraph rather than as the tail of the statement
        // above it or the head of the one below.
        const above = afterLine > 0 && lines[afterLine - 1].trim().length > 0;
        const below = afterLine < lines.length && lines[afterLine].trim().length > 0;
        const body = statements.map((one) => indent + one).join("\n");
        return root.replaceRange(
            offset, offset, (above ? "\n" : "") + body + "\n" + (below ? "\n" : ""));
    }

    // An import goes with the other imports — under the last one, or at the top
    // under a shebang. A file's imports are a block, and one adrift in the
    // middle of a scene is the kind of tidiness a tool owes.
    function insertImport(statement) {
        const lines = editor.text.split("\n");
        let at = 0;
        for (let i = 0; i < lines.length; ++i)
            if (/^\s*(import|from)\s/.test(lines[i]))
                at = i + 1;
        if (at === 0 && lines.length > 0 && lines[0].indexOf("#!") === 0)
            at = 1;

        let offset = 0;
        for (let i = 0; i < at; ++i)
            offset += lines[i].length + 1;

        const caret = editor.cursorPosition;
        editor.insert(offset, statement + "\n");
        editor.cursorPosition = caret >= offset ? caret + statement.length + 1 : caret;
    }

    // Apply an edit the way a person would have typed it.
    //
    // Through the document — remove, then insert — rather than by assigning the
    // whole text. Qt's undo stack records edits and ignores assignments, so a
    // gesture that replaced the buffer left ⌘Z with nothing to take back. This
    // way a drag and a keystroke share one history, which is the only way a
    // gesture and the code can be undone in the order they happened.
    function replaceRange(from, to, text) {
        if (from < 0 || to < from || to > editor.length)
            return false;

        const caret = editor.cursorPosition;
        // Through the shell, on the document itself: `remove` then `insert` from
        // here are two entries in the undo stack, and one ⌘Z left `side=` with
        // nothing after it.
        if (!Shell.replaceRange(editor.textDocument, from, to, text))
            return false;

        // The caret stays where it was, shifted by what the edit changed in
        // front of it: a gesture must not move the place you were typing.
        const delta = text.length - (to - from);
        editor.cursorPosition = caret > to ? caret + delta : caret;
        return true;
    }

    // Take the keyboard.
    //
    // `load()` asks for focus too, but a file opened from the menu is loaded
    // before the pane is brought to the front, and a request made while the pane
    // is behind another tab is a request nobody receives. Asked again by the
    // shell once the tab is up.
    function takeFocus() { editor.forceActiveFocus(); }

    // Whether the keys of the keyboard are currently letters.
    //
    // A text editor owns Space, the arrows, Home and End — they are how you
    // write — and a video editor owns exactly the same five for its transport.
    // Both are right, so the answer is WHO HAS THE CARET, and this is how the
    // rest of the chrome asks.
    readonly property bool typing: editor.activeFocus

    // Say something for a moment. The panel's one channel for news that has no
    // other home: a save refused, a rename that touched files you cannot see.
    function say(what) { notice.say(what); }

    // Something happened that you cannot see, said briefly and then gone.
    // A rename rewrites files nobody is looking at; a permanent strip for that
    // one sentence would cost a line of the pane forever.
    Rectangle {
        id: notice
        visible: false
        z: 14
        anchors { right: parent.right; rightMargin: 12; top: parent.top; topMargin: 10 }
        width: word.implicitWidth + 18
        height: 22
        radius: Theme.radiusSmall
        color: Theme.panel
        border.width: 1
        border.color: Theme.edge

        function say(what) {
            word.text = what;
            // A refusal is not good news, and green would say it was.
            word.color = /read-only|could not|nothing/.test(what) ? Theme.warn : Theme.ok;
            notice.visible = true;
            fade.restart();
        }

        Text {
            id: word
            anchors.centerIn: parent
            font.family: Theme.mono
            font.pixelSize: root.codeSize - 2
        }

        Timer {
            id: fade
            interval: 3000
            onTriggered: notice.visible = false
        }
    }

    // ── The new name ──────────────────────────────────────────────────────
    // A field over the word rather than a dialog in the middle of the screen:
    // what you are renaming is what you are looking at, and a modal would cover
    // it. F2 opens it with the old name selected, exactly as pressing it in any
    // other editor does.
    Rectangle {
        id: renaming
        visible: false
        z: 13
        width: 220
        height: 26
        color: Theme.panel
        radius: Theme.radiusSmall
        border.width: 1
        border.color: Theme.live

        function begin() {
            const from = root.wordStart();
            let to = editor.cursorPosition;
            while (to < editor.text.length && /[A-Za-z0-9_]/.test(editor.text.charAt(to)))
                ++to;
            if (to === from)
                return;

            const at = editor.mapToItem(root, editor.positionToRectangle(from).x, editor.cursorRectangle.y);
            renaming.x = Math.max(8, Math.min(at.x - 6, root.width - renaming.width - 8));
            renaming.y = Math.max(4, at.y - 4);
            field.text = editor.text.substring(from, to);
            renaming.visible = true;
            field.selectAll();
            field.forceActiveFocus();
        }

        function commit() {
            const at = root.locationAt(editor.cursorPosition);
            const wanted = field.text;
            renaming.visible = false;
            editor.forceActiveFocus();
            if (wanted.length === 0)
                return;
            Lsp.rename(root.path, at.line, at.character, wanted, function (edit) {
                const touched = root.applyEdit(edit);
                notice.say(touched === 0
                           ? "nothing to rename"
                           : "renamed in " + touched + (touched === 1 ? " file" : " files"));
                if (touched > 0 && root.path.length > 0)
                    Lsp.changeDocument(root.path, editor.text);
            });
        }

        TextField {
            id: field
            anchors.fill: parent
            anchors.margins: 3
            color: Theme.ink
            font.family: Theme.mono
            font.pixelSize: root.codeSize
            background: null
            onAccepted: renaming.commit()
            Keys.onEscapePressed: {
                renaming.visible = false;
                editor.forceActiveFocus();
            }
        }
    }

    // ── Everywhere a name is used ─────────────────────────────────────────
    // A list, not a jump: the point of asking is to see how many places there
    // are and what they look like before going anywhere. Each row carries the
    // line it found, because a path and a number alone tell you nothing.
    Rectangle {
        id: uses
        visible: false
        z: 12
        anchors { right: parent.right; rightMargin: 10; top: parent.top; topMargin: 10 }
        width: Math.min(420, root.width - 80)
        height: Math.min(found.count * 34 + 30, root.height - 60)
        color: Theme.codeSkin.hover
        radius: Theme.radiusSmall
        border.width: 1
        border.color: Theme.codeSkin.edge

        property var rows: []

        function offer(reply) {
            const items = root.listed(reply);
            // Reading a file once and slicing every hit out of it: a symbol
            // used forty times in one module is forty rows but one read.
            let cache = ({});
            let out = [];
            for (const item of items) {
                const where = item.uri.replace("file://", "");
                if (cache[where] === undefined)
                    cache[where] = (where === root.path ? editor.text : Shell.readTextFile(where)).split("\n");
                out.push({
                    path: where,
                    name: where.split("/").pop(),
                    line: item.range.start.line,
                    character: item.range.start.character,
                    body: (cache[where][item.range.start.line] !== undefined
                           ? cache[where][item.range.start.line] : "").trim()
                });
            }
            uses.rows = out;
            uses.visible = out.length > 0;
        }

        Text {
            id: count
            anchors { left: parent.left; leftMargin: 10; top: parent.top; topMargin: 8 }
            text: uses.rows.length + (uses.rows.length === 1 ? " use" : " uses")
            color: Theme.inkDim
            font.family: Theme.ui
            font.pixelSize: root.codeSize - 2
        }

        Text {
            anchors { right: parent.right; rightMargin: 10; top: parent.top; topMargin: 8 }
            text: "esc"
            color: Theme.inkFaint
            font.family: Theme.mono
            font.pixelSize: root.codeSize - 2
        }

        ListView {
            id: found
            anchors { fill: parent; topMargin: 24; margins: 1 }
            model: uses.rows
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            delegate: Rectangle {
                id: use
                required property var modelData
                width: found.width
                height: 34
                color: hit.containsMouse ? Theme.rail : "transparent"

                Text {
                    id: place
                    anchors { left: parent.left; leftMargin: 10; top: parent.top; topMargin: 4 }
                    text: use.modelData.name + ":" + (use.modelData.line + 1)
                    color: Theme.inkFaint
                    font.family: Theme.mono
                    font.pixelSize: root.codeSize - 2
                }

                Text {
                    anchors {
                        left: parent.left; leftMargin: 10; right: parent.right; rightMargin: 10
                        top: place.bottom; topMargin: 1
                    }
                    text: use.modelData.body
                    color: Theme.ink
                    font.family: Theme.mono
                    font.pixelSize: root.codeSize
                    elide: Text.ElideRight
                }

                MouseArea {
                    id: hit
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        uses.visible = false;
                        root.jump(use.modelData.path, use.modelData.line, use.modelData.character);
                    }
                }
            }
        }
    }

    // ── The call you are inside ───────────────────────────────────────────
    // Not a hover: it follows the caret, and what it emphasises changes with
    // every comma. Which argument you are on is the whole information — a
    // signature with no active parameter marked is just documentation.
    Rectangle {
        id: hint
        visible: false
        z: 11
        width: Math.min(shape.implicitWidth + 18, root.width - 24)
        height: shape.implicitHeight + 12
        color: Theme.codeSkin.hover
        radius: Theme.radiusSmall
        border.width: 1
        border.color: Theme.codeSkin.edge

        function offer(reply) {
            if (!reply || !reply.signatures || reply.signatures.length === 0) {
                hint.visible = false;
                return;
            }
            const chosen = reply.signatures[reply.activeSignature !== undefined ? reply.activeSignature : 0];
            if (chosen === undefined) {
                hint.visible = false;
                return;
            }
            shape.text = hint.emphasised(chosen, reply.activeParameter);
            const at = editor.mapToItem(root, editor.cursorRectangle.x, editor.cursorRectangle.y);
            hint.x = Math.max(8, Math.min(at.x - 20, root.width - hint.width - 8));
            // Above the caret, always: below is where the completion list goes,
            // and the two of them are often up at the same time.
            hint.y = Math.max(4, at.y - hint.height - 4);
            hint.visible = true;
        }

        // A parameter's label is either the text itself or a pair of offsets
        // into the signature — both are legal, and pyright sends offsets.
        function emphasised(signature, active) {
            const whole = signature.label;
            const index = signature.activeParameter !== undefined ? signature.activeParameter : active;
            const params = signature.parameters;
            if (!params || index === undefined || index === null || params[index] === undefined)
                return hint.plain(whole);

            const label = params[index].label;
            let from = -1;
            let to = -1;
            if (typeof label === "string") {
                from = whole.indexOf(label);
                to = from + label.length;
            } else if (label !== undefined && label.length === 2) {
                // A pair of offsets into the signature. Tested by length rather
                // than by Array.isArray, which is false for anything that came
                // across the bridge.
                from = label[0];
                to = label[1];
            }
            if (from < 0)
                return hint.plain(whole);

            return hint.plain(whole.substring(0, from))
                 + "<font color=\"" + Theme.live + "\"><b>" + hint.plain(whole.substring(from, to)) + "</b></font>"
                 + hint.plain(whole.substring(to));
        }

        // Styled text, so a default value holding < or & would otherwise eat
        // the rest of the signature.
        function plain(text) {
            return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        Text {
            id: shape
            anchors.fill: parent
            anchors.margins: 6
            color: Theme.codeSkin.ink
            font.family: Theme.mono
            font.pixelSize: root.codeSize
            textFormat: Text.StyledText
            wrapMode: Text.Wrap
        }
    }

    // ── What you could type next ──────────────────────────────────────────
    // The server is asked once per pause in typing, and the list is narrowed
    // locally on every keystroke after that. Asking again per character would
    // put a round trip between the key and the letter appearing, which is the
    // one thing an editor may never do.
    Rectangle {
        id: suggestions
        visible: false
        z: 11
        width: 340
        height: Math.min(list.count, 9) * 20 + 2
        color: Theme.codeSkin.hover
        radius: Theme.radiusSmall
        border.width: 1
        border.color: Theme.codeSkin.edge

        property var all: []
        property var shown: []

        function offer(items) {
            suggestions.all = items !== undefined && items !== null ? items : [];
            suggestions.refine();
        }

        function refine() {
            const prefix = editor.text.substring(root.wordStart(), editor.cursorPosition).toLowerCase();
            let out = [];
            for (const item of suggestions.all) {
                const label = (item.filterText !== undefined ? item.filterText : item.label).toLowerCase();
                if (prefix.length === 0 ? !label.startsWith("_") : label.startsWith(prefix))
                    out.push(item);
                // A module's namespace runs to thousands of names; past a
                // hundred nobody is reading, they are typing another letter.
                if (out.length >= 100)
                    break;
            }
            suggestions.shown = out;
            list.currentIndex = 0;
            suggestions.visible = out.length > 0;
            if (suggestions.visible)
                suggestions.place();
        }

        function place() {
            const at = editor.mapToItem(root, editor.positionToRectangle(root.wordStart()).x,
                                        editor.cursorRectangle.y + editor.cursorRectangle.height);
            suggestions.x = Math.max(8, Math.min(at.x, root.width - suggestions.width - 8));
            // Below the caret unless that would fall out of the pane, in which
            // case above it — never half-drawn at the bottom edge.
            suggestions.y = at.y + suggestions.height + 4 > root.height
                            ? at.y - suggestions.height - editor.cursorRectangle.height - 4
                            : at.y + 2;
        }

        function accept() {
            const item = suggestions.shown[list.currentIndex];
            if (item === undefined)
                return;
            // A snippet's placeholders are dropped rather than played out: the
            // pane has no tab-through-fields yet, and `Square(${1:side})` left
            // in the buffer is worse than no completion at all.
            let insert = item.insertText !== undefined ? item.insertText : item.label;
            if (item.insertTextFormat === 2)
                insert = insert.replace(/\$\{\d+:([^}]*)\}/g, "$1").replace(/\$\d+/g, "");
            const from = root.wordStart();
            editor.remove(from, editor.cursorPosition);
            editor.insert(from, insert);
            suggestions.visible = false;
        }

        ListView {
            id: list
            anchors.fill: parent
            anchors.margins: 1
            model: suggestions.shown
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            delegate: Rectangle {
                id: row
                required property var modelData
                required property int index
                width: list.width
                height: 20
                color: row.index === list.currentIndex ? Theme.rail : "transparent"

                Text {
                    id: glyph
                    anchors { left: parent.left; leftMargin: 7; verticalCenter: parent.verticalCenter }
                    width: 10
                    text: root.kindMark(row.modelData.kind)
                    color: root.kindColor(row.modelData.kind)
                    font.family: Theme.mono
                    font.pixelSize: root.codeSize - 2
                }

                Text {
                    id: label
                    anchors { left: glyph.right; leftMargin: 6; verticalCenter: parent.verticalCenter }
                    text: row.modelData.label
                    color: Theme.codeSkin.ink
                    font.family: Theme.mono
                    font.pixelSize: root.codeSize
                }

                // The signature, when there is room for it. Greyed, because it
                // is what you read second — after finding the name you meant.
                Text {
                    anchors {
                        left: label.right; leftMargin: 8
                        right: parent.right; rightMargin: 7
                        verticalCenter: parent.verticalCenter
                    }
                    text: row.modelData.detail !== undefined ? row.modelData.detail : ""
                    color: Theme.inkFaint
                    font.family: Theme.mono
                    font.pixelSize: root.codeSize - 2
                    elide: Text.ElideRight
                    horizontalAlignment: Text.AlignRight
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        list.currentIndex = row.index;
                        suggestions.accept();
                    }
                }
            }
        }
    }

    // Room to scroll PAST the end — a whole viewport of it, so the last line can
    // be brought to the top of the pane.
    //
    // The line you are writing is almost never the one you want at the bottom
    // edge of the screen: you want it where your eyes already are, with room to
    // think below it. Every editor worth the name does this; VS Code calls it
    // scrollBeyondLastLine and has it on.
    //
    // It is the FLICKABLE that is given the room, not the text item. Padding the
    // TextArea by a viewport's height is the obvious way and it breaks the
    // rendering outright — everything past the first line stops being drawn.
    // A margin on the thing that scrolls adds the same space and touches neither
    // the text nor the buffer, so the file on disk still ends where the code
    // ends.
    Binding {
        target: view.contentItem
        property: "bottomMargin"
        value: Math.max(root.height - gutter.lineHeight, 0)
        when: view.contentItem !== null
    }

    ScrollView {
        id: view
        anchors {
            left: gutter.right; right: parent.right
            top: filebar.bottom; bottom: parent.bottom
        }
        clip: true

        // The bubble is placed once, in panel coordinates, and does not scroll
        // with the line it explains — so a scroll leaves it pointing at
        // whatever slid under it. Dropped rather than followed: that is what
        // the editors this is modelled on do.
        Connections {
            target: view.contentItem
            function onContentYChanged() { probe.dismiss(); }
        }

        TextArea {
            id: editor
            color: Theme.codeSkin.ink
            font.family: Theme.mono
            font.pixelSize: 12
            selectByMouse: true
            background: null
            // The gap between the numbers and the first character. Wider than
            // the obvious 8: a number and a letter that nearly touch read as one
            // word, and every editor leaves a hand's breadth there.
            leftPadding: 14
            topPadding: 6
            // Code is not prose: a wrapped line lies about where the line ends,
            // and every editor a person has used before this one scrolls instead.
            wrapMode: TextEdit.NoWrap
            // Clicking under the last line is still clicking in the file. A
            // TextArea only as tall as its text leaves that band to the
            // Flickable, which takes the press and does nothing with it; one at
            // least as tall as the viewport hands it to the text, which puts the
            // caret on the nearest character — the end of the last line.
            height: Math.max(implicitHeight, view.availableHeight)
            selectionColor: Qt.alpha(Theme.ai, 0.35)
            selectedTextColor: Theme.ink
            persistentSelection: true

            // Which line the caret is on, counted once per move rather than
            // measured from pixels: the highlight and the gutter must agree even
            // while the view is scrolling.
            readonly property int currentLine: text.substring(0, cursorPosition).split("\n").length - 1

            // What the agent changed, behind the glyphs like the caret band and
            // for the same reason. One rectangle per touched line, in the
            // buffer's own coordinates, so it scrolls with the text for free.
            Repeater {
                model: root.diffRows

                Rectangle {
                    id: touched
                    required property int index
                    required property var modelData
                    z: -1
                    x: 0
                    y: touched.index * gutter.lineHeight
                    width: Math.max(view.width, editor.contentWidth)
                    height: gutter.lineHeight
                    visible: touched.modelData.kind !== "same"
                    // Tinted rather than solid: a full-strength green under
                    // monospaced text is a line you cannot read, and the point
                    // of the colour is to let you read it.
                    color: touched.modelData.kind === "add"
                           ? Qt.rgba(0.31, 0.75, 0.53, 0.18)
                           : Qt.rgba(0.88, 0.38, 0.36, 0.18)
                }
            }

            // The band under the caret, drawn behind the text (z < 0) so it
            // never touches the glyphs.
            Rectangle {
                z: -1
                x: 0
                y: editor.cursorRectangle.y
                width: Math.max(view.width, editor.contentWidth)
                height: editor.cursorRectangle.height
                color: Theme.codeSkin.band
                visible: editor.activeFocus
            }

            // Only a human's edit dirties the buffer: assigning the initial text
            // fires onTextChanged too, and counting that as a modification made
            // the pane open claiming an edit nobody had made.
            //
            // What the buffer looked like when nobody had touched it. `ready`
            // alone was not enough: attaching the syntax highlighter marks the
            // document changed, and QSyntaxHighlighter runs its first pass on a
            // later tick — after the flag was set — so the panel opened claiming
            // an edit nobody had made. Comparing the text catches that, because
            // colouring changes the formatting and never a character.
            property bool ready: false
            // Not `baseline`: that is one of Item's anchor lines and it is FINAL,
            // so the panel refused to load at all.
            property string pristine: ""

            Component.onCompleted: {
                pristine = text;
                root.document = editor.textDocument;
                root.documentReady(editor.textDocument);
                ready = true;
            }

            // Changing theme has to reach the text that is already painted, and
            // the palette lives outside this panel — so the panel offers its
            // document again and the shell repaints it.
            Connections {
                target: Theme
                function onCodeThemeChanged() { root.documentReady(editor.textDocument); }
            }

            // Arrowing away, or clicking elsewhere, is the same statement as
            // moving the mouse away: the bubble is about somewhere you no
            // longer are.
            onCursorPositionChanged: probe.dismiss()

            onTextChanged: {
                // A hover describes the word it was asked about, and typing has
                // just moved that word. Every editor drops it on the first
                // keystroke rather than leaving stale prose over live code.
                probe.dismiss();

                if (!ready || text === pristine)
                    return;
                root.modified = true;

                // The author has written something of their own, so the agent's
                // turn stops being one thing to undo: a ⌘Z that swallowed both
                // would take work nobody asked it to take. The key goes back to
                // being the editor's own undo from here.
                Agent.disarm();

                // Narrowing happens now, on the letter just typed; asking the
                // server happens after the pause. The list therefore never
                // shows a name that no longer matches what is on screen.
                if (suggestions.visible)
                    suggestions.refine();
                const just = editor.text.charAt(editor.cursorPosition - 1);
                if (root.path.length > 0 && /[A-Za-z0-9_.]/.test(just))
                    ask.restart();
                else
                    suggestions.visible = false;

                // Opening a call asks what it takes; a comma asks again,
                // because the answer is which argument you are now on. Closing
                // it ends the question.
                if (root.path.length === 0)
                    return;
                if (just === "(" || just === ",")
                    askSignature.restart();
                else if (just === ")")
                    hint.visible = false;
            }

            Timer {
                id: askSignature
                interval: 160
                onTriggered: {
                    const at = root.locationAt(editor.cursorPosition);
                    Lsp.signatureHelp(root.path, at.line, at.character, function (reply) { hint.offer(reply); });
                }
            }

            // The pause after which the buffer is worth an opinion. It also
            // gives Main's handler time to push the edit to the server: asking
            // about text the server has not been told about answers about the
            // text before it.
            Timer {
                id: ask
                interval: 160
                onTriggered: {
                    const at = root.locationAt(editor.cursorPosition);
                    Lsp.completion(root.path, at.line, at.character, function (reply) {
                        // Either a bare list or { isIncomplete, items } — both
                        // shapes are legal and pyright uses the second.
                        suggestions.offer(reply && reply.items !== undefined ? reply.items : reply);
                    });
                }
            }

            // ── Hovering a symbol ─────────────────────────────────────────
            // Declared BEFORE the squiggles so they sit above it: over a
            // squiggle the message wins, everywhere else the type wins. Asking
            // the server on every mouse move would be a request per pixel, so
            // the pointer has to come to rest first.
            MouseArea {
                id: probe
                anchors.fill: parent
                // Clicks are taken only to be handed straight back: ⌘-click
                // follows a definition, and a press with no modifier is
                // refused, which passes it up to the text where it belongs.
                acceptedButtons: Qt.LeftButton
                hoverEnabled: true

                onPressed: (mouse) => {
                    if (!(mouse.modifiers & Qt.ControlModifier) || root.path.length === 0) {
                        mouse.accepted = false;
                        return;
                    }
                    const at = root.locationAt(editor.positionAt(mouse.x, mouse.y));
                    Lsp.definition(root.path, at.line, at.character, function (reply) { root.follow(reply); });
                }

                property real lastX: 0
                property real lastY: 0

                // Every reply the server sends answers a question about a
                // POSITION, and the pointer has usually moved on by the time it
                // lands. Without a token the late answer painted a bubble for a
                // word the mouse had already left — and nothing was left to
                // hide it, so it stayed until the next hover. Bumping this on
                // every move, exit and dismissal makes a stale reply arrive
                // holding the wrong number, and drop itself.
                property int token: 0

                function dismiss() {
                    probe.token++;
                    dwell.stop();
                    tip.hide();
                }

                onPositionChanged: (mouse) => {
                    // Reaching INTO the bubble must not close it: VS Code lets
                    // you walk onto a hover to read it, and a bubble that fled
                    // the pointer could never be read at all. The rectangle is
                    // in the panel's coordinates and the mouse in the text's.
                    if (tip.visible) {
                        const at = editor.mapToItem(root, mouse.x, mouse.y);
                        if (at.x >= tip.x - 4 && at.x <= tip.x + tip.width + 4
                            && at.y >= tip.y - 6 && at.y <= tip.y + tip.height + 4)
                            return;
                    }
                    probe.lastX = mouse.x;
                    probe.lastY = mouse.y;
                    probe.dismiss();
                    dwell.restart();
                }

                onExited: probe.dismiss()

                Timer {
                    id: dwell
                    interval: 400
                    onTriggered: {
                        if (root.path.length === 0)
                            return;
                        const offset = editor.positionAt(probe.lastX, probe.lastY);
                        const at = root.locationAt(offset);
                        const anchor = editor.positionToRectangle(offset);
                        const mine = ++probe.token;
                        Lsp.hover(root.path, at.line, at.character, function (reply) {
                            if (mine !== probe.token)
                                return;
                            tip.show(root.readable(reply), anchor.x, anchor.y + anchor.height);
                        });
                    }
                }
            }

            // ── The squiggles ─────────────────────────────────────────────
            // Children of the TextArea rather than of the ScrollView, so they
            // scroll with the text for free — the same reason the current-line
            // band lives here. Under the glyphs would hide them, so they sit at
            // the default z and are drawn as a thin wave along the baseline.
            Repeater {
                model: root.shownDiagnostics

                Item {
                    id: squiggle
                    required property var modelData

                    // A diagnostic that spans lines is underlined on its first
                    // line only: a wave running down the left margin of three
                    // lines says nothing the first line did not already say.
                    readonly property int startLine: squiggle.modelData.range.start.line
                    readonly property rect head: editor.positionToRectangle(
                        root.offsetOf(squiggle.startLine, squiggle.modelData.range.start.character))
                    readonly property rect tail: editor.positionToRectangle(
                        squiggle.modelData.range.end.line === squiggle.startLine
                        ? root.offsetOf(squiggle.startLine, squiggle.modelData.range.end.character)
                        : root.offsetOf(squiggle.startLine + 1, 0) - 1)

                    x: squiggle.head.x
                    y: squiggle.head.y
                    // An empty range still has to be visible, or a diagnostic
                    // pointing at a missing character marks nothing at all.
                    width: Math.max(squiggle.tail.x - squiggle.head.x, 6)
                    height: squiggle.head.height

                    Canvas {
                        id: wave
                        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                        height: 3

                        onPaint: {
                            const ctx = getContext("2d");
                            ctx.reset();
                            ctx.strokeStyle = root.severityColor(squiggle.modelData.severity);
                            ctx.lineWidth = 1;
                            ctx.beginPath();
                            // Period of four pixels: shorter reads as a dotted
                            // line at this font size, longer as a scribble.
                            for (let x = 0; x <= width; ++x)
                                ctx.lineTo(x, 1.5 + Math.sin(x * Math.PI / 2) * 1.2);
                            ctx.stroke();
                        }

                        onWidthChanged: wave.requestPaint()
                    }

                    // Reading the message must not cost the caret its place, so
                    // the strip hovers and never takes a click.
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.NoButton
                        hoverEnabled: true
                        ToolTip.visible: containsMouse
                        ToolTip.delay: 350
                        ToolTip.text: squiggle.modelData.message
                    }
                }
            }

            Keys.onPressed: (event) => {
                // While the list is up it owns the keys it needs and nothing
                // else — the arrows, the two ways of accepting, and escape.
                // Everything else falls through and keeps typing, which is what
                // narrows the list.
                if (suggestions.visible) {
                    if (event.key === Qt.Key_Down) {
                        list.incrementCurrentIndex();
                        event.accepted = true;
                        return;
                    }
                    if (event.key === Qt.Key_Up) {
                        list.decrementCurrentIndex();
                        event.accepted = true;
                        return;
                    }
                    if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Tab) {
                        suggestions.accept();
                        event.accepted = true;
                        return;
                    }
                    if (event.key === Qt.Key_Escape) {
                        suggestions.visible = false;
                        event.accepted = true;
                        return;
                    }
                }

                if (event.key === Qt.Key_Escape && uses.visible) {
                    uses.visible = false;
                    event.accepted = true;
                    return;
                }

                // Each of these is ASKED of Keymap rather than spelled out here,
                // so the keyboard board and this handler cannot drift apart:
                // rebinding writes one string and both follow it.
                if (root.path.length > 0) {
                    const at = root.locationAt(editor.cursorPosition);

                    if (Keymap.matches(event, "definition")) {
                        Lsp.definition(root.path, at.line, at.character, function (reply) { root.follow(reply); });
                        event.accepted = true;
                        return;
                    }
                    if (Keymap.matches(event, "references")) {
                        Lsp.references(root.path, at.line, at.character, function (reply) { uses.offer(reply); });
                        event.accepted = true;
                        return;
                    }
                    if (Keymap.matches(event, "rename")) {
                        renaming.begin();
                        event.accepted = true;
                        return;
                    }
                    if (Keymap.matches(event, "complete")) {
                        ask.restart();
                        event.accepted = true;
                        return;
                    }
                    if (Keymap.matches(event, "save")) {
                        root.saveRequested();
                        event.accepted = true;
                        return;
                    }
                    if (Keymap.matches(event, "execute")) {
                        root.executeRequested();
                        event.accepted = true;
                        return;
                    }
                }
                // ⌘ arrives as ControlModifier and ⌃ as MetaModifier: Qt swaps
                // the two on macOS so that a shortcut written once lands on the
                // key a Mac user expects. So ⌘← is ControlModifier here, and
                // ⌃Space below is MetaModifier — reading them the other way
                // round silently binds nothing.
                if (Keymap.matches(event, "back")) {
                    root.goBack();
                    event.accepted = true;
                    return;
                }
                if (Keymap.matches(event, "forward")) {
                    root.goForward();
                    event.accepted = true;
                    return;
                }

                // Tab is four spaces, because the buffer is Python and a stray
                // tab character is a syntax error waiting for the next editor to
                // open the file.
                if (event.key === Qt.Key_Tab) {
                    editor.insert(editor.cursorPosition, "    ");
                    event.accepted = true;
                }
            }
        }
    }
}
