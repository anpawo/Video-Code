"""
The League of Legends tutorial, as a template: an intro card, the champion's clips grouped in
sections with captions, one music track under all of it. A champion's video is only data:

    tutorial(
        champion="Tahm Kench", role="Top",
        intro="media/tahm-kench/intro.mp4",
        sections=[
            Section("Advanced Combo", [
                Clip("media/tahm-kench/combo.mp4", [(0.5, "Q flash to stun or finish"), ...]),
            ]),
        ],
        music="media/tahm-kench/music.m4a",
    )

A clip or an intro given no file plays a blank of `seconds`, labelled with its slot, so the
whole video can be laid out before any footage exists.

Modelled on "Focus on : Tahm Kench Top" (youtu.be/3hwarq5CSCU): no voice, the tips are captions
at the foot of the frame, each section is a chapter of the video. Clips inside a section are
joined by `clipTransition`, sections by `sectionTransition`.
"""

import os
import subprocess
from dataclasses import dataclass, field
from typing import Callable

from videocode import *
from videocode.template.effect.other.transitions import dipToBlack, filmBurn, flash, whipPan

INK = WHITE
DIM = rgba(200, 204, 214)
ACCENT = rgba(200, 170, 110)  # the gold of the game's own UI
SHADE = rgba(8, 10, 14)
BLANK = "1b1f27"
GRID = "262c37"

Transition = Callable[..., object]


@dataclass
class Clip:
    path: str | None = None
    # (second in the clip, text); each caption stays until the next one, or `hold` seconds
    captions: list[tuple[sec, str]] = field(default_factory=list)
    seconds: sec = 6.0  # the blank's length, when there is no file yet
    hold: sec = 3.0


@dataclass
class Section:
    title: str
    clips: list[Clip]


def blank(seconds: sec) -> str:
    """A dark clip of `seconds`, made once and kept in ~/.cache/videocode."""
    # one grid cell per world unit: a flat colour would make every transition between blanks invisible
    path = os.path.expanduser(f"~/.cache/videocode/blank-grid-{seconds:g}s.mp4")
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x{BLANK}:s=1280x720:r={FRAMERATE}:d={seconds},drawgrid=w=80:h=80:t=2:c=0x{GRID}",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", path],
            check=True,
        )
    return path


def footage(path: str | None, seconds: sec, slot: str | None = None) -> Video:
    clip = Video(path or blank(seconds), width=W, height=H)
    if path is None and slot:
        Text(text=slot, fontSize=0.4, fillColor=DIM).position(0, 0.2) \
            .fadeIn(duration=0.3).wait(max(seconds - 0.6, 0)).fadeOut(duration=0.3)
    return clip


def caption(text: str, at: sec, until: sec) -> None:
    Text(text=text, fontSize=0.3, fillColor=INK).position(0, -3.85) \
        .wait(at).fadeIn(duration=0.15).wait(max(until - at - 0.3, 0)).fadeOut(duration=0.15)


def sectionTag(title: str) -> None:
    tag = Text(text=title.upper(), fontSize=0.3, fillColor=ACCENT)
    tag.position(-W / 2 + 0.5 + tag.width / 2, H / 2 - 0.5).wait(0.3).fadeIn(duration=0.3).wait(2.2).fadeOut(duration=0.3)


def titles(champion: str, role: str, seconds: sec) -> None:
    for text, size, color, y in (("FOCUS ON", 0.34, ACCENT, 1.3), (champion.upper(), 1.3, INK, 0.2), (f"{role} · tips and tricks", 0.34, DIM, -0.9)):
        Text(text=text, fontSize=size, fillColor=color, bold=size > 1).position(0, y) \
            .fadeIn(duration=0.5).wait(max(seconds - 1.2, 0)).fadeOut(duration=0.4)


def until(second: sec) -> None:
    # wait() only waits for the animations: a transition must also wait for its footage
    wait()
    if second > Context.cursor / FRAMERATE:
        wait(second - Context.cursor / FRAMERATE)


def tutorial(
    champion: str,
    role: str,
    sections: list[Section],
    music: str | None = None,
    intro: str | None = None,
    introSeconds: sec = 4,
    musicVolume: float = 0.5,
    outro: str = "and stay safe",
    clipTransition: Transition = whipPan,
    sectionTransition: Transition = flash,
    transitionSeconds: sec = 0.4,
) -> None:
    track = Sound(music, volume=musicVolume) if music else None
    d = transitionSeconds

    # the intro opens the first chapter: YouTube drops every chapter when one is under ten seconds
    timestamp(sections[0].title)
    shown = footage(intro, introSeconds + d)
    Rectangle(width=W, height=H, fillColor=SHADE, strokeColor=TRANSPARENT).opacity(140).wait(introSeconds).fadeOut(duration=d)
    titles(champion, role, introSeconds)

    for n, section in enumerate(sections):
        for i, clip in enumerate(section.clips):
            until(introSeconds if not n and not i else shown.end - d)
            if n and not i:
                timestamp(section.title)
            incoming = footage(clip.path, clip.seconds, f"CLIP · {section.title} {i + 1}").hide()
            join = filmBurn if not n and not i else sectionTransition if not i else clipTransition
            join(shown, incoming, duration=d if join is not filmBurn else 2 * d)
            if not i:
                sectionTag(section.title)
            times = [t for t, _ in clip.captions]
            for k, (at, text) in enumerate(clip.captions):
                caption(text, at, times[k + 1] if k + 1 < len(times) else at + clip.hold)
            shown = incoming

    until(shown.end - d)
    card = Rectangle(width=W, height=H, fillColor=SHADE, strokeColor=TRANSPARENT).hide()
    dipToBlack(shown, card, duration=d)
    Text(text=outro, fontSize=0.5, fillColor=INK).position(0, 0.2).wait(d).fadeIn(duration=0.6)
    if track:
        track.over(duration=2.5).volume = 0
    wait(2.5)
