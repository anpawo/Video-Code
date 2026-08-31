// The mark that says what kind of thing this is, drawn the same everywhere.
//
// Video, image and sound are drawn rather than typed. Unicode's marks for them
// are made to sit on a text baseline, so the play triangle comes out tall and
// narrow, the note comes out as hairlines, and ◆ says "diamond" where the rest
// of the world draws a framed photograph. Drawn, they are one set: same weight,
// same optical size, same rounding.
pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: root

    property string kind: "video"
    property color tint: Theme.inkDim
    property real size: 10

    // Only the two marks a typeface gets wrong are drawn; the rest are
    // characters, because a good glyph already exists for them.
    readonly property var characters: ({
        "polygon": "≋", "subs": "T"
    })

    readonly property bool drawn: kind === "video" || kind === "image" || kind === "sound"

    implicitWidth: size
    implicitHeight: size

    Canvas {
        id: mark
        anchors.centerIn: parent
        visible: root.drawn
        // A sideways equilateral triangle is only 0.866 × its side across, so the
        // video box is not square and the glyph is centred rather than stretched.
        width: root.kind === "video" ? root.size * 0.866 : root.size
        height: root.size

        onPaint: {
            const ctx = getContext("2d");
            ctx.reset();
            ctx.fillStyle = root.tint;
            ctx.strokeStyle = root.tint;

            if (root.kind === "video") {
                // Rounded on all three corners by stroking the path with a round
                // join before filling it: the stroke fattens the shape by half
                // its width, so the triangle is inset by exactly that much and
                // ends up the size it was asked for.
                const r = Math.max(root.size * 0.16, 1);
                const w = width - r;
                const h = height - r;
                ctx.lineJoin = "round";
                ctx.lineCap = "round";
                ctx.lineWidth = r;
                ctx.beginPath();
                ctx.moveTo(r / 2, r / 2);
                ctx.lineTo(r / 2, h);
                ctx.lineTo(w, height / 2);
                ctx.closePath();
                ctx.stroke();
                ctx.fill();
                return;
            }

            if (root.kind === "image") {
                // The picture mark everyone already knows: a frame with a sun and
                // a mountain in it. Punched OUT of the filled frame rather than
                // drawn on top, so it reads at nine pixels on any background —
                // two thin strokes at that size are a smudge.
                const r = root.size * 0.2;
                ctx.beginPath();
                ctx.moveTo(r, 0);
                ctx.lineTo(width - r, 0);
                ctx.quadraticCurveTo(width, 0, width, r);
                ctx.lineTo(width, height - r);
                ctx.quadraticCurveTo(width, height, width - r, height);
                ctx.lineTo(r, height);
                ctx.quadraticCurveTo(0, height, 0, height - r);
                ctx.lineTo(0, r);
                ctx.quadraticCurveTo(0, 0, r, 0);
                ctx.closePath();
                ctx.fill();

                ctx.globalCompositeOperation = "destination-out";

                ctx.beginPath();
                ctx.arc(width * 0.32, height * 0.33, width * 0.12, 0, Math.PI * 2);
                ctx.closePath();
                ctx.fill();

                ctx.beginPath();
                ctx.moveTo(width * 0.12, height * 0.8);
                ctx.lineTo(width * 0.45, height * 0.42);
                ctx.lineTo(width * 0.66, height * 0.62);
                ctx.lineTo(width * 0.78, height * 0.5);
                ctx.lineTo(width * 0.95, height * 0.8);
                ctx.closePath();
                ctx.fill();
                return;
            }

            // An eighth note, built the way one is written: an oval head lying on
            // a slant, a stem off its right shoulder, a flag falling from the
            // top. The tilt is the whole point — a head drawn level reads as a
            // blob with a stick, which is what the last attempt looked like.
            const stem = Math.max(root.size * 0.12, 1.2);

            ctx.save();
            ctx.translate(width * 0.36, height * 0.74);
            ctx.rotate(-0.38);
            ctx.beginPath();
            ctx.ellipse(-width * 0.26, -height * 0.19, width * 0.52, height * 0.38);
            ctx.closePath();
            ctx.fill();
            ctx.restore();

            ctx.lineCap = "round";
            ctx.lineWidth = stem;
            ctx.beginPath();
            ctx.moveTo(width * 0.6, height * 0.72);
            ctx.lineTo(width * 0.6, height * 0.12);
            ctx.stroke();

            // The flag: out and down from the top of the stem, thick where it
            // leaves and thin where it lands.
            ctx.beginPath();
            ctx.moveTo(width * 0.6, height * 0.1);
            ctx.quadraticCurveTo(width * 1.02, height * 0.2, width * 0.86, height * 0.5);
            ctx.quadraticCurveTo(width * 0.88, height * 0.26, width * 0.6, height * 0.3);
            ctx.closePath();
            ctx.fill();
        }

        // A Canvas does not repaint because a colour bound into onPaint changed.
        Connections {
            target: root
            function onTintChanged() { mark.requestPaint(); }
            function onSizeChanged() { mark.requestPaint(); }
            function onKindChanged() { mark.requestPaint(); }
        }
    }

    Text {
        anchors.centerIn: parent
        visible: !root.drawn
        text: root.characters[root.kind] !== undefined ? root.characters[root.kind] : "•"
        color: root.tint
        font.pixelSize: root.size * 1.1
    }
}
