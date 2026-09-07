#pragma once

#include <memory>
#include <string>

namespace VC
{
    // The preview's loudspeaker: one WAV, decoded into memory, with a cursor.
    //
    // It looks like a player and never like a file — `load`, `play`, `pause`,
    // `seek`, `position` — so the day the WAV is replaced by an in-process
    // mixer, nothing above this line moves. Decoded whole rather than streamed
    // because the file is rewritten under it after every run.
    class Speaker
    {
    public:

        Speaker();
        ~Speaker();

        bool load(const std::string& path);
        void unload();
        bool loaded() const;

        void   play(double at);
        void   pause();
        void   seek(double at);
        double position() const; // seconds, -1 when nothing is loaded
        bool   playing() const;

        void setMuted(bool muted);

        bool muted() const { return _muted; }

        const std::string& why() const { return _why; }

    private:

        struct Impl;
        std::unique_ptr<Impl> _impl;
        bool                  _muted = false;
        std::string           _why;
    };
} // namespace VC
