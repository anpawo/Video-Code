// A key, drawn rather than typed.
//
// `⇧` and the arrows come out of a text font as whatever that font happens to
// have: thin, hollow, a different weight from the letters beside them, and a
// different shape in the next font along. Every keyboard picture worth looking
// at draws them instead — so these are strokes, at the size and colour they are
// asked for, and they look the same everywhere.
//
// On a `Canvas` and not `QtQuick.Shapes`: this build of Qt has no Shapes
// module, and a glyph that needs a module the binary does not carry is a glyph
// that does not appear. Eleven pixels of polyline cost nothing to raster.
//
// Anything this file does not know how to draw answers `drawn: false`, and the
// caller writes the character instead: `⌘`, `⌥` and `⌃` are unmistakable in
// every font on this machine, and a hand-drawn `⌘` would be a worse `⌘`.
import QtQuick

Item {
    id: root

    // The token as the keymap spells it, or the character it maps to.
    property string token: ""
    property color ink: "white"
    property real weight: 1.3

    // Each glyph is a list of strokes; each stroke a list of points in a 12×12
    // box, and `closed` when the last point joins the first.
    readonly property var strokes: ({
        "⇧": [{ closed: true, at: [[6, 1.2], [10.8, 6], [8.6, 6], [8.6, 10.8], [3.4, 10.8], [3.4, 6], [1.2, 6]] }],
        "←": [{ at: [[10.5, 6], [2.2, 6]] }, { at: [[5.2, 3], [2.2, 6], [5.2, 9]] }],
        "→": [{ at: [[1.5, 6], [9.8, 6]] }, { at: [[6.8, 3], [9.8, 6], [6.8, 9]] }],
        "↑": [{ at: [[6, 10.5], [6, 2.2]] }, { at: [[3, 5.2], [6, 2.2], [9, 5.2]] }],
        "↓": [{ at: [[6, 1.5], [6, 9.8]] }, { at: [[3, 6.8], [6, 9.8], [9, 6.8]] }],
        "⇥": [{ at: [[1.5, 6], [8, 6]] }, { at: [[5.8, 3.8], [8, 6], [5.8, 8.2]] }, { at: [[10.2, 2.6], [10.2, 9.4]] }],
        "⏎": [{ at: [[10.2, 2.4], [10.2, 6], [2.6, 6]] }, { at: [[5, 3.6], [2.6, 6], [5, 8.4]] }],
        "⌫": [{ closed: true, at: [[10.5, 2.5], [4.6, 2.5], [1.2, 6], [4.6, 9.5], [10.5, 9.5]] },
              { at: [[6.2, 4.6], [9, 7.4]] }, { at: [[9, 4.6], [6.2, 7.4]] }]
    })

    readonly property bool drawn: root.strokes[root.token] !== undefined

    implicitWidth: 12
    implicitHeight: 12
    visible: root.drawn

    onTokenChanged: paper.requestPaint()
    onInkChanged: paper.requestPaint()

    Canvas {
        id: paper
        anchors.fill: parent
        antialiasing: true

        onPaint: {
            const ctx = getContext("2d");
            ctx.reset();
            if (!root.drawn)
                return;
            const unit = Math.min(width, height) / 12;
            ctx.strokeStyle = root.ink;
            ctx.lineWidth = root.weight * unit;
            ctx.lineCap = "round";
            ctx.lineJoin = "round";
            for (const stroke of root.strokes[root.token]) {
                ctx.beginPath();
                for (let i = 0; i < stroke.at.length; ++i) {
                    const point = stroke.at[i];
                    if (i === 0)
                        ctx.moveTo(point[0] * unit, point[1] * unit);
                    else
                        ctx.lineTo(point[0] * unit, point[1] * unit);
                }
                if (stroke.closed === true)
                    ctx.closePath();
                ctx.stroke();
            }
        }
    }
}
