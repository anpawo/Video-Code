#!/usr/bin/env python3
"""
The editor's preview has sound: after a run, the scene's audio graph — the
render's own `AudioGraph`, from compiler/AudioMix, the one `AudioArgs` wraps for
the export — is mixed into a WAV and the
`Speaker` (window/Speaker, miniaudio) holds it. Both are driven here through
the editor: a WAV with the wrong graph gives the wrong levels below, and a
Speaker that does not load, play or seek fails the cursor checks.

Checked through a windowless editor and `tell`, muted so nothing plays out
loud: the WAV exists, its levels have the shape the scene asked for (music,
music ducked under the voice, music back), a scene with no sound says so, and
mute answers. No window opens.

Run directly: `python3 test/preview_sound_test.py`
"""

import json
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, ".")
sys.path.insert(0, "test")

from helpers import check, needsTool, section, summary

if not needsTool("./video-code", "the editor is the built binary") or not needsTool("ffmpeg", "the preview mix is ffmpeg's"):
    summary()
    sys.exit(0)

SOCKET = f"/tmp/videocode-test-sound-{os.getpid()}.sock"
env = {**os.environ, "VC_SOCKET": SOCKET}


def tell(*args: str) -> tuple[bool, dict]:
    run = subprocess.run(["./video-code", "tell", *args], env=env, capture_output=True, text=True, timeout=60)
    try:
        return run.returncode == 0, json.loads(run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return False, {"error": (run.stdout + run.stderr)[-300:]}


def level(path: str, start: float, length: float) -> float:
    out = subprocess.run(
        ["ffmpeg", "-v", "info", "-ss", str(start), "-t", str(length), "-i", path, "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, timeout=60,
    ).stderr
    for line in out.splitlines():
        if "mean_volume:" in line:
            return float(line.split("mean_volume:")[1].split("dB")[0])
    return -999.0


def editor(scene: str) -> subprocess.Popen:
    return subprocess.Popen(
        ["./video-code", "--editor", "--check-chrome", "--serve", "--file", scene],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )


def settled(want_file: bool) -> dict:
    deadline = time.time() + 40
    answer: dict = {}
    while time.time() < deadline:
        time.sleep(0.5)
        ok, answer = tell("audio")
        if ok and not answer.get("baking") and (bool(answer.get("file")) == want_file or answer.get("why")):
            return answer
    return answer


with tempfile.TemporaryDirectory() as tmp:
    ducked = os.path.join(tmp, "ducked.py")
    with open(ducked, "w") as f:
        f.write(
            "from videocode import *\n"
            "wait(1)\n"
            "music = Sound('test/tour_music.wav', volume=0.6)\n"
            "voice = Sound('test/test_speech.wav', start=2.5)\n"
            "music.duck(under=voice, to=0.12, fade=0.3)\n"
            "wait(8.5)\n"
        )
    if not os.path.exists("test/tour_music.wav"):
        # The tour writes it; written here the same way when the tour has not run.
        subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0,'docs/by-example'); import tour"], capture_output=True, timeout=120)
    quiet = os.path.join(tmp, "quiet.py")
    with open(quiet, "w") as f:
        f.write("from videocode import *\nSquare(side=1)\nwait(1)\n")

    section("a scene with a duck: the preview WAV is baked and loaded, muted")
    proc = editor(ducked)
    try:
        # Muted as soon as the editor answers — before anything could be
        # played out loud on the machine running the suite.
        deadline = time.time() + 30
        ok = False
        while time.time() < deadline and not ok:
            time.sleep(0.3)
            ok, _ = tell("mute", "on=true")
        answer = settled(True)
        wav = answer.get("file", "")
        check(f"the mix is baked into a WAV ({wav})", bool(wav) and os.path.exists(wav))
        check("and the speaker holds it (hasAudio)", answer.get("hasAudio") is True and answer.get("why", "") == "")
        check("mute is on for the test", answer.get("muted") is True)
        if wav and os.path.exists(wav):
            before, during, after = level(wav, 1.2, 1.2), level(wav, 3.6, 2.2), level(wav, 6.5, 2.4)
            check(f"music before ({before:.1f} dB) and after the voice ({after:.1f} dB) are the same level", abs(before - after) < 1.0)
            check(f"the voice over the ducked music is louder ({during:.1f} dB)", during > before + 1.0)
        ok, state = tell("state")
        check("tell state says the sound is ready", ok and state.get("sound") == "ready")
        ok, answer = tell("play")
        time.sleep(0.6)
        ok, answer = tell("audio")
        check(f"playing, the speaker's cursor moves ({answer.get('position')} s)", ok and answer.get("position", 0) > 0.2)
        ok, _ = tell("pause")
        ok, answer = tell("seek", "at=5")
        ok, answer = tell("audio")
        check(f"a seek moves the cursor with the head ({answer.get('position')} s)", ok and abs(answer.get("position", 0) - 5) < 0.2)
        tell("quit")
        proc.wait(timeout=10)
        check("the WAV is swept away with the editor", not os.path.exists(wav))
    finally:
        if proc.poll() is None:
            proc.kill()

    section("a scene with no sound says so, and bakes nothing")
    proc = editor(quiet)
    try:
        answer = settled(False)
        check("nothing to hear: hasAudio is false and no reason is given", answer.get("hasAudio") is False and answer.get("why", "") == "" and not answer.get("file"))
        ok, state = tell("state")
        check("tell state says none", ok and state.get("sound") == "none")
        tell("quit")
        proc.wait(timeout=10)
    finally:
        if proc.poll() is None:
            proc.kill()
    if os.path.exists(SOCKET):
        os.unlink(SOCKET)

summary()
