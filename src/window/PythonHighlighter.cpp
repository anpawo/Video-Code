/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** PythonHighlighter
*/

#include "window/PythonHighlighter.hpp"

#include <QColor>

namespace
{
    // The two halves of Python's keyword list, kept apart because they mean
    // different things to a reader: what the program DOES at this point, and
    // what this point IS.  Colouring them alike throws that away.
    const QStringList kFlow = {
        "if", "elif", "else", "for", "while", "break", "continue", "return",
        "yield", "pass", "raise", "try", "except", "finally", "with", "as",
        "assert", "await", "match", "case", "import", "from"
    };

    // `import` and `from` sit with the flow words rather than here, because
    // that is where VS Code puts them: they are `keyword.control`, the same
    // scope as `if` and `return`, and they carry its hue.  `def` and `class`
    // are `storage.type` — what this point IS — and keep the other one.
    const QStringList kDeclaration = {
        "def", "class", "lambda", "global", "nonlocal", "async", "del"
    };

    // `True`/`False`/`None` are `constant.language`; `self`/`cls` are
    // `variable.language`, which the theme paints differently.  They were one
    // list here, which made two of the five the wrong colour.
    const QStringList kConstant = {"True", "False", "None"};

    const QStringList kSelf = {"self", "cls"};

    const QStringList kOperatorWord = {"and", "or", "not", "in", "is"};

    QString wordsToPattern(const QStringList& words)
    {
        return QStringLiteral("\\b(?:%1)\\b").arg(words.join(QLatin1Char('|')));
    }
} // namespace

VC::PythonHighlighter::PythonHighlighter(QTextDocument* document, const QVariantMap& colours)
    : QSyntaxHighlighter(document)
{
    recolour(colours);
}

void VC::PythonHighlighter::recolour(const QVariantMap& colours)
{
    _colours = colours;
    _rules.clear();

    _stringFormat = colour(QStringLiteral("string"));
    // Not italic.  A comment is already set apart by its colour, and a slanted
    // face in a monospaced grid is the one thing that makes a column of code
    // stop lining up — VS Code leaves it upright too.
    _commentFormat = colour(QStringLiteral("comment"));

    // Order matters: the last rule to paint a range wins, so the specific ones
    // come after the general ones.  Strings and comments are not rules at all —
    // they are painted afterwards, over everything, because a keyword inside a
    // string is not a keyword.
    _rules.push_back({QRegularExpression(wordsToPattern(kFlow)), colour(QStringLiteral("flow")), 0});
    _rules.push_back({QRegularExpression(wordsToPattern(kDeclaration)), colour(QStringLiteral("keyword")), 0});
    _rules.push_back({QRegularExpression(wordsToPattern(kOperatorWord)), colour(QStringLiteral("flow")), 0});
    _rules.push_back({QRegularExpression(wordsToPattern(kConstant)), colour(QStringLiteral("constant")), 0});
    _rules.push_back({QRegularExpression(wordsToPattern(kSelf)), colour(QStringLiteral("caps")), 0});

    // Numbers, including 1.5, 1e3 and 0x1f — a video scene is mostly numbers.
    _rules.push_back({QRegularExpression(QStringLiteral("\\b(?:0[xX][0-9a-fA-F]+|\\d+\\.?\\d*(?:[eE][+-]?\\d+)?)\\b")), colour(QStringLiteral("number")), 0});

    // A call, and the name a def gives it: the two ways a function appears.
    _rules.push_back({QRegularExpression(QStringLiteral("\\b([A-Za-z_]\\w*)\\s*\\(")), colour(QStringLiteral("call")), 1});
    _rules.push_back({QRegularExpression(QStringLiteral("\\bdef\\s+([A-Za-z_]\\w*)")), colour(QStringLiteral("call")), 1});
    _rules.push_back({QRegularExpression(QStringLiteral("\\bclass\\s+([A-Za-z_]\\w*)")), colour(QStringLiteral("type")), 1});

    // A CamelCase name is a CLASS, and it is painted apart from a function —
    // `Square(...)` is not the same kind of thing as `moveBy(...)`, and every
    // editor shows that.  VS Code knows it from the language server's semantic
    // tokens; here it is read off the name, which in Python is not a guess:
    // PEP 8 spells classes CapWords and everything else lower_case.
    //
    // AFTER the call rule, so `Square(` loses its "call" colour and keeps this
    // one, and one lower-case letter is required so that a name in capitals
    // stays a constant rather than becoming a class.
    _rules.push_back({QRegularExpression(QStringLiteral("\\b[A-Z][A-Za-z0-9_]*[a-z][A-Za-z0-9_]*\\b")), colour(QStringLiteral("type")), 0});

    // An argument passed BY NAME — `width=1.5` — which is how nearly every line
    // of a scene reads.
    //
    // The `(` or `,` in front is what makes it an argument rather than any name
    // before an `=`.  Without it the rule also caught the default value in a
    // signature (`duration: sec = 0.4` painted `sec`), which VS Code leaves
    // plain — and a hover full of colours the editor beside it does not use is
    // exactly the mismatch this pane is trying not to have.
    _rules.push_back({QRegularExpression(QStringLiteral("[(,]\\s*([A-Za-z_]\\w*)\\s*=(?!=)")), colour(QStringLiteral("argument")), 1});

    // A NAME IN CAPITALS is a constant, and every editor paints it apart —
    // VS Code tags it `variable.other.constant` and gives it its own hue,
    // which is why WHITE, GREEN_A and RED_B stood out there and not here.
    // Two characters minimum, so a lone `A` in an expression stays text; the
    // pattern cannot swallow a class name, because CamelCase has lower-case
    // letters in it and this one may not.
    _rules.push_back({QRegularExpression(QStringLiteral("\\b_*[A-Z][A-Z0-9_]+\\b")), colour(QStringLiteral("caps")), 0});

    _rules.push_back({QRegularExpression(QStringLiteral("@[A-Za-z_][\\w.]*")), colour(QStringLiteral("call")), 0});
}

QTextCharFormat VC::PythonHighlighter::colour(const QString& key, bool italic) const
{
    QTextCharFormat format;
    const QVariant  value = _colours.value(key);

    if (value.isValid())
        format.setForeground(QColor(value.toString()));
    format.setFontItalic(italic);
    return format;
}

void VC::PythonHighlighter::highlightBlock(const QString& text)
{
    for (const Rule& rule : _rules) {
        auto matches = rule.pattern.globalMatch(text);
        while (matches.hasNext()) {
            const QRegularExpressionMatch match = matches.next();
            setFormat(match.capturedStart(rule.group), match.capturedLength(rule.group), rule.format);
        }
    }

    // The analyser's answer, over the guess — but under the strings, because a
    // name inside a string is not a name.
    for (const Span& span : _tokens.value(currentBlock().blockNumber()))
        if (span.format.foreground().style() != Qt::NoBrush)
            setFormat(span.column, span.length, span.format);

    paintStrings(text);
}

void VC::PythonHighlighter::setTokens(const QVariantList& spans)
{
    _tokens.clear();

    for (const QVariant& entry : spans) {
        const QVariantMap     span = entry.toMap();
        const QTextCharFormat format = formatFor(
            span.value(QStringLiteral("kind")).toString(),
            span.value(QStringLiteral("modifiers")).toStringList()
        );
        if (format.foreground().style() == Qt::NoBrush)
            continue;

        _tokens[span.value(QStringLiteral("line")).toInt()].append(
            Span{span.value(QStringLiteral("column")).toInt(), span.value(QStringLiteral("length")).toInt(), format}
        );
    }

    rehighlight();
}

// The analyser's vocabulary, mapped onto the palette's.
//
// Only the kinds that SAY something are painted.  A plain variable is left as
// text on purpose — colouring every name is how a screen stops having any
// emphasis at all, and it is what VS Code does too.
QTextCharFormat VC::PythonHighlighter::formatFor(const QString& kind, const QStringList& modifiers) const
{
    if (kind == "class" || kind == "type" || kind == "enum" || kind == "typeParameter" || kind == "interface" || kind == "struct")
        return colour(QStringLiteral("type"));

    if (kind == "function" || kind == "method" || kind == "decorator")
        return colour(QStringLiteral("call"));

    if (kind == "parameter" || kind == "property")
        return colour(QStringLiteral("argument"));

    if (kind == "selfParameter" || kind == "clsParameter")
        return colour(QStringLiteral("caps"));

    if (kind == "keyword")
        return colour(QStringLiteral("keyword"));

    // A constant is a variable that cannot be written to — which is exactly what
    // the capitals convention was standing in for.
    if (kind == "variable" && modifiers.contains(QStringLiteral("readonly")))
        return colour(QStringLiteral("caps"));

    // A plain variable has its own hue, one step off the body text — and a
    // namespace is a type over there, not a variable.
    if (kind == "variable")
        return colour(QStringLiteral("variable"));

    if (kind == "namespace")
        return colour(QStringLiteral("type"));

    if (kind == "enumMember")
        return colour(QStringLiteral("caps"));

    return {};
}

void VC::PythonHighlighter::paintStrings(const QString& text)
{
    static const QRegularExpression triple(QStringLiteral("\"\"\"|'''"));
    static const QRegularExpression single(
        QStringLiteral("(\"(?:\\\\.|[^\"\\\\])*\"|'(?:\\\\.|[^'\\\\])*')")
    );
    static const QRegularExpression comment(QStringLiteral("#[^\n]*"));

    setCurrentBlockState(0);

    int start = 0;
    // Carried over from the block before: this line opened inside a docstring,
    // so it is a string until the closing quotes, whatever else is on it.
    if (previousBlockState() == 1) {
        const QRegularExpressionMatch close = triple.match(text);
        if (!close.hasMatch()) {
            setFormat(0, text.length(), _stringFormat);
            setCurrentBlockState(1);
            return;
        }
        setFormat(0, close.capturedEnd(), _stringFormat);
        start = close.capturedEnd();
    }

    // Ordinary strings first, so a # inside one is not read as a comment.
    auto quoted = single.globalMatch(text, start);
    int  lastQuotedEnd = start;
    while (quoted.hasNext()) {
        const QRegularExpressionMatch match = quoted.next();
        setFormat(match.capturedStart(), match.capturedLength(), _stringFormat);
        lastQuotedEnd = match.capturedEnd();
    }

    // A docstring opening on this line and never closing on it.
    const QRegularExpressionMatch open = triple.match(text, start);
    if (open.hasMatch() && open.capturedStart() >= lastQuotedEnd) {
        const QRegularExpressionMatch close = triple.match(text, open.capturedEnd());
        if (close.hasMatch()) {
            setFormat(open.capturedStart(), close.capturedEnd() - open.capturedStart(), _stringFormat);
        } else {
            setFormat(open.capturedStart(), text.length() - open.capturedStart(), _stringFormat);
            setCurrentBlockState(1);
            return;
        }
    }

    // Comments last and outermost: everything after a # that is not itself
    // inside a string belongs to the human, not to Python.
    auto comments = comment.globalMatch(text);
    while (comments.hasNext()) {
        const QRegularExpressionMatch match = comments.next();
        if (format(match.capturedStart()) == _stringFormat)
            continue;
        setFormat(match.capturedStart(), match.capturedLength(), _commentFormat);
    }
}
