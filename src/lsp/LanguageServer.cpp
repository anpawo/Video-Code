/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** LanguageServer
*/

#include "lsp/LanguageServer.hpp"

#include <QJsonArray>
#include <QJsonDocument>
#include <QQmlEngine>
#include <QStandardPaths>
#include <QUrl>

VC::LanguageServer::LanguageServer(QObject* parent)
    : QObject(parent)
{
    connect(&_server, &QProcess::readyReadStandardOutput, this, &LanguageServer::readAvailable);

    connect(&_server, &QProcess::errorOccurred, this, [this](QProcess::ProcessError) {
        // Not while we are the ones killing it. Quitting terminates the child,
        // which reports an error on the way out, and announcing that pyright
        // "could not be started" as the window closes is a lie about a failure
        // that never happened — it is what Control-C used to print.
        if (_stopping)
            return;

        Q_EMIT failed(QStringLiteral(
            "pyright-langserver could not be started — `pip install pyright` puts it on the path."
        ));
    });
}

VC::LanguageServer::~LanguageServer()
{
    _stopping = true;

    if (_server.state() != QProcess::NotRunning) {
        // A language server left running holds an analysis of a project nobody
        // has open any more.
        _server.terminate();
        if (!_server.waitForFinished(1500))
            _server.kill();
    }
}

bool VC::LanguageServer::running() const
{
    return _ready;
}

QString VC::LanguageServer::uriFor(const QString& path)
{
    return QUrl::fromLocalFile(path).toString();
}

QString VC::LanguageServer::pathFor(const QString& uri)
{
    return QUrl(uri).toLocalFile();
}

void VC::LanguageServer::start(const QString& root)
{
    if (_server.state() != QProcess::NotRunning)
        return;

    _root = root;

    // basedpyright first, and pyright only if it is absent.  They are the same
    // analyser; the fork adds the one thing colouring needs — semantic tokens,
    // which say what a name IS rather than how it is spelled.  Without them a
    // class written in lower case reads as a function, and no lexical rule can
    // ever fix that.
    QString binary = QStandardPaths::findExecutable(QStringLiteral("basedpyright-langserver"));
    if (binary.isEmpty())
        binary = QStandardPaths::findExecutable(QStringLiteral("pyright-langserver"));
    if (binary.isEmpty()) {
        Q_EMIT failed(QStringLiteral(
            "No language server on the path — `pip install basedpyright` installs one."
        ));
        return;
    }

    _server.start(binary, {QStringLiteral("--stdio")});
    if (!_server.waitForStarted(5000)) {
        Q_EMIT failed(QStringLiteral("pyright-langserver did not start"));
        return;
    }

    // What we can do with what it sends back. Declaring less than we support is
    // the safe direction: the server then simply does not offer it.
    QJsonObject text;
    text.insert("hover", QJsonObject{{"contentFormat", QJsonArray{"markdown", "plaintext"}}});
    text.insert("definition", QJsonObject{{"linkSupport", false}});
    text.insert("references", QJsonObject{});
    text.insert("rename", QJsonObject{{"prepareSupport", false}});
    text.insert("completion", QJsonObject{{"completionItem", QJsonObject{{"snippetSupport", false}, {"documentationFormat", QJsonArray{"markdown", "plaintext"}}}}});
    text.insert("signatureHelp", QJsonObject{{"signatureInformation", QJsonObject{{"documentationFormat", QJsonArray{"markdown", "plaintext"}}}}});
    text.insert("publishDiagnostics", QJsonObject{{"relatedInformation", false}});

    // Semantic tokens: what a name IS, answered by the analyser rather than
    // guessed from its spelling.  The legend — which number means "class" — is
    // the server's to declare, so ours is left empty and read back from the
    // initialize result.
    text.insert(
        "semanticTokens",
        QJsonObject{
            {"requests", QJsonObject{{"full", true}}},
            {"tokenTypes", QJsonArray{}},
            {"tokenModifiers", QJsonArray{}},
            {"formats", QJsonArray{"relative"}}
        }
    );
    text.insert("synchronization", QJsonObject{{"didSave", false}, {"willSave", false}, {"dynamicRegistration", false}});

    QJsonObject folder;
    folder.insert("uri", uriFor(root));
    folder.insert("name", QStringLiteral("scene"));

    QJsonObject params;
    params.insert("processId", QJsonValue());
    params.insert("rootUri", uriFor(root));
    params.insert("workspaceFolders", QJsonArray{folder});
    // The server ASKS for its settings rather than being told: declaring this
    // is what lets workspace/configuration arrive at all, and without it the
    // analyser runs on its own defaults — which for basedpyright are far
    // stricter than the ones this project is written against.
    params.insert(
        "capabilities",
        QJsonObject{
            {"textDocument", text},
            {"workspace", QJsonObject{{"configuration", true}}}
        }
    );

    request(QStringLiteral("initialize"), params, QJSValue());
}

// How the analyser is asked to judge this project, when it asks.
//
// These mirror the author's VS Code — `basic` type checking, and the rule about
// an expression whose value is thrown away silenced.
//
// They are the FALLBACK, not the decision.  A pyrightconfig.json in the project
// takes precedence over everything sent here, and this project has one; that is
// where the rules actually live, because they have to hold for `make typecheck`
// and CI as much as for this pane.  Measured, not assumed: silencing a rule from
// here alone changed nothing while the config file existed.
QJsonObject VC::LanguageServer::settingsFor(const QString& section) const
{
    const QJsonObject analysis{
        {"typeCheckingMode", QStringLiteral("basic")},
        {"diagnosticSeverityOverrides",
         QJsonObject{{"reportUnusedExpression", QStringLiteral("none")}}}
    };

    if (section == QLatin1String("python.analysis") || section == QLatin1String("basedpyright.analysis"))
        return analysis;

    if (section == QLatin1String("python") || section == QLatin1String("basedpyright"))
        return QJsonObject{{"analysis", analysis}};

    return {};
}

void VC::LanguageServer::semanticTokens(const QString& path)
{
    if (_tokenTypes.isEmpty())
        return;

    request(
        QStringLiteral("textDocument/semanticTokens/full"),
        QJsonObject{{"textDocument", QJsonObject{{"uri", uriFor(path)}}}},
        QJSValue()
    );
    // The id is remembered rather than a callback, because the answer is not for
    // QML: it goes to the highlighter as a signal, whole.
    _tokenRequests.insert(_nextId - 1, path);
}

// The wire format is five integers per token, and every one of them is a DELTA:
// lines from the previous token, columns from the previous token on that same
// line, then length, type and modifiers.  Decoded here rather than in QML
// because a file of any size is thousands of integers, and handing those across
// the bridge one array at a time costs more than the colouring is worth.
QVariantList VC::LanguageServer::decodeTokens(const QJsonArray& data) const
{
    QVariantList spans;
    int          line = 0;
    int          column = 0;

    for (int i = 0; i + 4 < data.size(); i += 5) {
        const int deltaLine = data.at(i).toInt();
        const int deltaStart = data.at(i + 1).toInt();
        const int length = data.at(i + 2).toInt();
        const int type = data.at(i + 3).toInt();
        const int modifiers = data.at(i + 4).toInt();

        line += deltaLine;
        column = deltaLine == 0 ? column + deltaStart : deltaStart;

        if (type < 0 || type >= _tokenTypes.size())
            continue;

        QStringList held;
        for (int bit = 0; bit < _tokenModifiers.size(); ++bit)
            if (modifiers & (1 << bit))
                held << _tokenModifiers.at(bit);

        spans.append(QVariantMap{{"line", line}, {"column", column}, {"length", length}, {"kind", _tokenTypes.at(type)}, {"modifiers", held}});
    }

    return spans;
}

void VC::LanguageServer::restart(const QString& root)
{
    if (root == _root && _server.state() != QProcess::NotRunning)
        return;

    if (_server.state() != QProcess::NotRunning) {
        // Ours to kill, so its error on the way out is not news.
        _stopping = true;
        _server.terminate();
        if (!_server.waitForFinished(1500))
            _server.kill();
        _stopping = false;
    }

    // Everything the old process knew goes with it: pending callbacks would be
    // answered by nobody, and the version numbers belong to its copy of the
    // files, not to the new one's.
    _ready = false;
    _inbox.clear();
    _pending.clear();
    _versions.clear();
    _tokenRequests.clear();
    _tokenTypes.clear();
    _tokenModifiers.clear();

    start(root);
}

void VC::LanguageServer::send(const QJsonObject& message)
{
    if (_server.state() != QProcess::Running)
        return;

    QJsonObject full = message;
    full.insert("jsonrpc", QStringLiteral("2.0"));

    const QByteArray body = QJsonDocument(full).toJson(QJsonDocument::Compact);
    _server.write("Content-Length: " + QByteArray::number(body.size()) + "\r\n\r\n");
    _server.write(body);
}

void VC::LanguageServer::request(const QString& method, const QJsonObject& params, QJSValue then)
{
    const int id = _nextId++;
    if (then.isCallable())
        _pending.insert(id, then);

    send(QJsonObject{{"id", id}, {"method", method}, {"params", params}});
}

void VC::LanguageServer::notify(const QString& method, const QJsonObject& params)
{
    send(QJsonObject{{"method", method}, {"params", params}});
}

void VC::LanguageServer::readAvailable()
{
    _inbox.append(_server.readAllStandardOutput());

    // Content-Length framing: a header block, a blank line, then exactly that
    // many bytes. Several messages can arrive in one read, and one message can
    // arrive in several — so the buffer is drained only when a whole one is in.
    for (;;) {
        const int split = _inbox.indexOf("\r\n\r\n");
        if (split < 0)
            return;

        int length = -1;
        for (const QByteArray& line : _inbox.left(split).split('\n')) {
            const QByteArray header = line.trimmed().toLower();
            if (header.startsWith("content-length:"))
                length = header.mid(15).trimmed().toInt();
        }
        if (length < 0)
            return;

        const int start = split + 4;
        if (_inbox.size() < start + length)
            return;

        const QByteArray body = _inbox.mid(start, length);
        _inbox.remove(0, start + length);

        const QJsonDocument parsed = QJsonDocument::fromJson(body);
        if (parsed.isObject())
            dispatch(parsed.object());
    }
}

void VC::LanguageServer::dispatch(const QJsonObject& message)
{
    // An answer to something we asked.
    if (message.contains("id") && (message.contains("result") || message.contains("error"))) {
        const int id = message.value("id").toInt();

        if (!_ready && !_pending.contains(id) && message.contains("result") && message.value("result").toObject().contains("capabilities")) {
            _ready = true;
            notify(QStringLiteral("initialized"), QJsonObject{});

            QStringList       offered;
            const QJsonObject capabilities =
                message.value("result").toObject().value("capabilities").toObject();

            // The legend says which number means "class".  It is the server's
            // to declare, and it differs between servers, so it is read here
            // rather than assumed anywhere else.
            const QJsonObject legend = capabilities.value("semanticTokensProvider")
                                           .toObject()
                                           .value("legend")
                                           .toObject();
            for (const QJsonValue& type : legend.value("tokenTypes").toArray())
                _tokenTypes.append(type.toString());
            for (const QJsonValue& modifier : legend.value("tokenModifiers").toArray())
                _tokenModifiers.append(modifier.toString());

            for (auto it = capabilities.begin(); it != capabilities.end(); ++it)
                offered << it.key();
            Q_EMIT ready(offered);
            return;
        }

        if (_tokenRequests.contains(id)) {
            const QString path = _tokenRequests.take(id);
            Q_EMIT tokens(path, decodeTokens(message.value("result").toObject().value("data").toArray()));
            return;
        }

        if (!_pending.contains(id))
            return;

        QJSValue   then = _pending.take(id);
        QJSEngine* engine = qjsEngine(this);
        if (!engine)
            return;

        const QJsonValue result = message.value("result");
        then.call({engine->toScriptValue(result.toVariant())});
        return;
    }

    // Something the server ASKS US.  A request has both an id and a method; it
    // must be answered, or a server that waits for the answer stops analysing.
    if (message.contains("id") && message.contains("method")) {
        const QString asked = message.value("method").toString();

        if (asked == QLatin1String("workspace/configuration")) {
            QJsonArray answer;
            for (const QJsonValue& item : message.value("params").toObject().value("items").toArray())
                answer.append(settingsFor(item.toObject().value("section").toString()));
            send(QJsonObject{{"id", message.value("id")}, {"result", answer}});
            return;
        }

        // Everything else is answered with nothing, which is a valid answer and
        // keeps the server moving.
        send(QJsonObject{{"id", message.value("id")}, {"result", QJsonValue()}});
        return;
    }

    // Something the server tells us of its own accord.
    const QString method = message.value("method").toString();
    if (method != QStringLiteral("textDocument/publishDiagnostics"))
        return;

    const QJsonObject params = message.value("params").toObject();
    QVariantList      items;
    for (const QJsonValue& item : params.value("diagnostics").toArray())
        items.append(item.toObject().toVariantMap());

    Q_EMIT diagnostics(pathFor(params.value("uri").toString()), items);
}

void VC::LanguageServer::openDocument(const QString& path, const QString& text)
{
    // Opening a file that is already open is an edit, not an open.  The pane
    // opens a document when it loads one and again when the server comes up,
    // and a second didOpen for one URI is a protocol error the server is
    // entitled to answer by dropping the file.
    if (_versions.contains(path)) {
        changeDocument(path, text);
        return;
    }

    _versions.insert(path, 1);

    QJsonObject document;
    document.insert("uri", uriFor(path));
    document.insert("languageId", QStringLiteral("python"));
    document.insert("version", 1);
    document.insert("text", text);

    notify(QStringLiteral("textDocument/didOpen"), QJsonObject{{"textDocument", document}});
}

void VC::LanguageServer::changeDocument(const QString& path, const QString& text)
{
    const int version = _versions.value(path, 1) + 1;
    _versions.insert(path, version);

    QJsonObject document;
    document.insert("uri", uriFor(path));
    document.insert("version", version);

    notify(QStringLiteral("textDocument/didChange"), QJsonObject{{"textDocument", document}, {"contentChanges", QJsonArray{QJsonObject{{"text", text}}}}});
}

void VC::LanguageServer::closeDocument(const QString& path)
{
    _versions.remove(path);
    notify(QStringLiteral("textDocument/didClose"), QJsonObject{{"textDocument", QJsonObject{{"uri", uriFor(path)}}}});
}

// ── The questions ───────────────────────────────────────────────────────────
namespace
{
    QJsonObject at(const QString& uri, int line, int character)
    {
        return QJsonObject{
            {"textDocument", QJsonObject{{"uri", uri}}},
            {"position", QJsonObject{{"line", line}, {"character", character}}}
        };
    }
} // namespace

void VC::LanguageServer::hover(const QString& path, int line, int character, QJSValue then)
{
    request(QStringLiteral("textDocument/hover"), at(uriFor(path), line, character), then);
}

void VC::LanguageServer::definition(const QString& path, int line, int character, QJSValue then)
{
    request(QStringLiteral("textDocument/definition"), at(uriFor(path), line, character), then);
}

void VC::LanguageServer::completion(const QString& path, int line, int character, QJSValue then)
{
    request(QStringLiteral("textDocument/completion"), at(uriFor(path), line, character), then);
}

void VC::LanguageServer::signatureHelp(const QString& path, int line, int character, QJSValue then)
{
    request(QStringLiteral("textDocument/signatureHelp"), at(uriFor(path), line, character), then);
}

void VC::LanguageServer::references(const QString& path, int line, int character, QJSValue then)
{
    QJsonObject params = at(uriFor(path), line, character);
    params.insert("context", QJsonObject{{"includeDeclaration", true}});
    request(QStringLiteral("textDocument/references"), params, then);
}

void VC::LanguageServer::rename(const QString& path, int line, int character, const QString& newName, QJSValue then)
{
    QJsonObject params = at(uriFor(path), line, character);
    params.insert("newName", newName);
    request(QStringLiteral("textDocument/rename"), params, then);
}
