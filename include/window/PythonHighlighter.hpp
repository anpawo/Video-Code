/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** PythonHighlighter
*/

#pragma once

#include <QHash>
#include <QRegularExpression>
#include <QSyntaxHighlighter>
#include <QTextCharFormat>
#include <QVariantList>
#include <QVariantMap>
#include <vector>

namespace VC
{
    // -----------------------------------------------------------------------
    // PythonHighlighter
    //   Colours the scene buffer in the editor's Code panel.
    //
    //   Why C++ for something the chrome could fake
    //   ───────────────────────────────────────────
    //   Qt Quick has no syntax highlighter.  A TextArea can be handed rich text,
    //   but then every keystroke has to re-mark up the whole buffer in JS and the
    //   cursor fights the markup — an editor that stutters while you type is
    //   worse than one with no colours.  QSyntaxHighlighter re-highlights only
    //   the blocks that changed, and it plugs into the QTextDocument that already
    //   backs the TextArea, so the chrome only has to hand it over.
    //
    //   Where the colours come from
    //   ───────────────────────────
    //   Not from here.  They are passed in from Theme.qml, so the palette stays
    //   in one file and the code panel cannot drift from the rest of the chrome.
    // -----------------------------------------------------------------------
    class PythonHighlighter : public QSyntaxHighlighter
    {
        Q_OBJECT

    public:

        // The document owns the highlighter, so it dies with the panel it was
        // attached to — which is what makes reloading the chrome safe.
        explicit PythonHighlighter(QTextDocument* document, const QVariantMap& colours);
        ~PythonHighlighter() override = default;

        // recolour() — same rules, new palette.  Switching theme must not mean
        // attaching a second highlighter to the same document: two of them paint
        // the same text twice and the loser wins at random.
        void recolour(const QVariantMap& colours);

        // setTokens() — what the language server says each name IS.
        //
        // The rules below are a GUESS made from spelling, and a good one: they
        // paint instantly, on every keystroke, with no round trip.  These are
        // the answer, and they arrive a moment later — so they are painted last
        // and win wherever they exist.  Where the analyser has nothing to say,
        // which is every symbol re-exported through a package's __init__, the
        // guess is still there underneath.
        //
        // Each entry is { line, column, length, kind, modifiers }, zero-based.
        void setTokens(const QVariantList& spans);

    protected:

        void highlightBlock(const QString& text) override;

    private:

        struct Rule
        {
            QRegularExpression pattern;
            QTextCharFormat    format;
            // Which capture to paint: 0 is the whole match, 1 the first group —
            // how `def name` colours the name and not the keyword again.
            int group = 0;
        };

        // colour() — a format built from the palette, falling back to plain ink
        // so a missing entry loses a colour rather than the whole panel.
        QTextCharFormat colour(const QString& key, bool italic = false) const;

        // formatFor() — the palette entry a token kind is painted with, or an
        // empty format for the kinds that are better left as plain text.
        QTextCharFormat formatFor(const QString& kind, const QStringList& modifiers) const;

        struct Span
        {
            int             column = 0;
            int             length = 0;
            QTextCharFormat format;
        };

        // Kept by line, because that is the only question highlightBlock asks.
        QHash<int, QVector<Span>> _tokens;

        // paintStrings() — the one thing rules cannot do alone.
        //
        // A triple-quoted string spans blocks, and a block knows nothing of its
        // neighbours unless it is told: the previous block's state is the only
        // memory a QSyntaxHighlighter has, so an unterminated """ leaves a mark
        // that the next block reads.
        void paintStrings(const QString& text);

        QVariantMap       _colours;
        std::vector<Rule> _rules;
        QTextCharFormat   _stringFormat;
        QTextCharFormat   _commentFormat;
    };
} // namespace VC
