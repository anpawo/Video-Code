#define MINIAUDIO_IMPLEMENTATION
#include "window/Speaker.hpp"

#include <miniaudio.h>

struct VC::Speaker::Impl
{
    ma_engine engine{};
    bool      engineUp = false;
    ma_sound  sound{};
    bool      loaded = false;
};

VC::Speaker::Speaker() : _impl(std::make_unique<Impl>()) {}

VC::Speaker::~Speaker()
{
    unload();
    if (_impl->engineUp)
        ma_engine_uninit(&_impl->engine);
}

bool VC::Speaker::load(const std::string& path)
{
    // The device is opened at the first sound, not at launch: a scene with
    // nothing to hear never touches CoreAudio, and a windowless run neither.
    if (!_impl->engineUp) {
        if (ma_engine_init(nullptr, &_impl->engine) != MA_SUCCESS) {
            _why = "no audio device would open";
            return false;
        }
        _impl->engineUp = true;
    }
    unload();
    if (ma_sound_init_from_file(&_impl->engine, path.c_str(), MA_SOUND_FLAG_DECODE, nullptr, nullptr, &_impl->sound) != MA_SUCCESS) {
        _why = "the preview mix could not be decoded";
        return false;
    }
    _impl->loaded = true;
    _why.clear();
    ma_sound_set_volume(&_impl->sound, _muted ? 0.0f : 1.0f);
    return true;
}

void VC::Speaker::unload()
{
    if (!_impl->loaded)
        return;
    ma_sound_uninit(&_impl->sound);
    _impl->loaded = false;
}

bool VC::Speaker::loaded() const { return _impl->loaded; }

void VC::Speaker::play(double at)
{
    if (!_impl->loaded)
        return;
    seek(at);
    ma_sound_start(&_impl->sound);
}

void VC::Speaker::pause()
{
    if (_impl->loaded)
        ma_sound_stop(&_impl->sound);
}

void VC::Speaker::seek(double at)
{
    if (!_impl->loaded)
        return;
    const ma_uint32 rate = ma_engine_get_sample_rate(&_impl->engine);
    ma_sound_seek_to_pcm_frame(&_impl->sound, (ma_uint64)(std::max(0.0, at) * rate));
}

double VC::Speaker::position() const
{
    if (!_impl->loaded)
        return -1.0;
    float seconds = 0.0f;
    if (ma_sound_get_cursor_in_seconds(&_impl->sound, &seconds) != MA_SUCCESS)
        return -1.0;
    return seconds;
}

bool VC::Speaker::playing() const { return _impl->loaded && ma_sound_is_playing(&_impl->sound); }

void VC::Speaker::setMuted(bool muted)
{
    _muted = muted;
    if (_impl->loaded)
        ma_sound_set_volume(&_impl->sound, muted ? 0.0f : 1.0f);
}
