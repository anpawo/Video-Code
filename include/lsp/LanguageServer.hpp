/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** LanguageServer
*/

#pragma once

#include <QHash>
#include <QJSValue>
#include <QJsonArray>
#include <QJsonObject>
#include <QObject>
#include <QProcess>
#include <QString>
#include <QVariantList>

namespace VC
{
    // -----------------------------------------------------------------------
    // LanguageServer
    //   What the code pane knows about Python, and about videocode.
    //
    //   Everything an editor is expected to know — where a name is defined, what
    //   a call takes, what a docstring says, what is wrong on line 40 — is
    //   answered by a language server over LSP.  Not by the editor, and not by
    //   VS Code: LSP is a protocol, and pyright speaks it standing alone.  This
    //   class is the whole of our side of it.
    //
    //   Shape
    //   ─────
    //   JSON-RPC over the server's stdin/stdout, framed by Content-Length.
    //   Requests carry an id and are answered out of order, so each one keeps
    //   the QML callback that is waiting for it.  Notifications (diagnostics)
    //   arrive unasked and are emitted as signals.
    //
    //   The pane sends the buffer's WHOLE text on every change.  Incremental
    //   sync exists and is what a large file would want; a scene is two hundred
    //   lines and the difference is not measurable, while the bug it avoids —
    //   the server's copy drifting from ours — is the worst kind.
    // -----------------------------------------------------------------------
    class LanguageServer : public QObject
    {
        Q_OBJECT

    public:

        explicit LanguageServer(QObject* parent = nullptr);
        ~LanguageServer() override;

        // start() — spawn the server for a project root.  Idempotent.
        Q_INVOKABLE void start(const QString& root);

        // restart() — point the analyser at a different project.  A server's
        // root is fixed at initialize, so opening another folder means a new
        // process: there is no message that moves one.
        Q_INVOKABLE void restart(const QString& root);

        // ── The document, as the server sees it ─────────────────────────────
        Q_INVOKABLE void openDocument(const QString& path, const QString& text);
        Q_INVOKABLE void changeDocument(const QString& path, const QString& text);
        Q_INVOKABLE void closeDocument(const QString& path);

        // ── Questions, each answered by calling back ────────────────────────
        // Positions are zero-based, as the protocol has them; the pane converts.
        Q_INVOKABLE void hover(const QString& path, int line, int character, QJSValue then);
        Q_INVOKABLE void definition(const QString& path, int line, int character, QJSValue then);
        Q_INVOKABLE void completion(const QString& path, int line, int character, QJSValue then);
        Q_INVOKABLE void signatureHelp(const QString& path, int line, int character, QJSValue then);
        Q_INVOKABLE void references(const QString& path, int line, int character, QJSValue then);
        Q_INVOKABLE void rename(const QString& path, int line, int character, const QString& newName, QJSValue then);

        // semanticTokens() — ask what every name in the file IS.  The answer
        // arrives on tokens(), not through a callback: it is for the
        // highlighter, and it is far too long to be worth crossing into QML as
        // a script value.
        Q_INVOKABLE void semanticTokens(const QString& path);

        Q_INVOKABLE bool running() const;

    Q_SIGNALS:

        // Sent by the server whenever it has re-checked a file, asked for or not.
        void diagnostics(const QString& path, const QVariantList& items);

        // Up, with the capabilities it advertised.
        void ready(const QStringList& capabilities);

        void failed(const QString& reason);

        // What the analyser says each name is: a list of
        // { line, column, length, kind, modifiers }, zero-based.
        void tokens(const QString& path, const QVariantList& spans);

    private:

        void send(const QJsonObject& message);
        void request(const QString& method, const QJsonObject& params, QJSValue then);
        void notify(const QString& method, const QJsonObject& params);
        void readAvailable();
        void dispatch(const QJsonObject& message);

        QVariantList decodeTokens(const QJsonArray& data) const;

        // settingsFor() — the answer to workspace/configuration.
        QJsonObject settingsFor(const QString& section) const;

        static QString uriFor(const QString& path);
        static QString pathFor(const QString& uri);

        QProcess _server;

        // True once we are taking the server down ourselves, so its dying breath is

        // not reported as a failure to start.

        bool                 _stopping = false;
        QByteArray           _inbox;
        int                  _nextId = 1;
        bool                 _ready = false;
        QString              _root;
        QHash<int, QJSValue> _pending;
        QHash<QString, int>  _versions;
        QStringList          _tokenTypes;
        QStringList          _tokenModifiers;
        QHash<int, QString>  _tokenRequests;
    };
} // namespace VC
