"""
Tahm Kench top, on the tutorial template. The clips and the music are cut from the published
video (youtu.be/3hwarq5CSCU) until new footage replaces them; they live in media/, which is
not committed.

    ./video-code --file videos/lol/tahm_kench.py --generate tahm_kench.mp4
"""

from videos.lol.tutorial import Clip, Section, tutorial

MEDIA = "videos/lol/media/tahm-kench"

tutorial(
    champion="Tahm Kench",
    role="Top",
    intro=f"{MEDIA}/intro.mp4",
    sections=[
        Section("Advanced Combo", [
            Clip(f"{MEDIA}/combo.mp4", [
                (0.8, "Q flash to stun, or to finish off an enemy"),
                (5.0, "always W right after the stun of the Q"),
            ]),
        ]),
        Section("Laning Phase", [
            Clip(f"{MEDIA}/laning.mp4", [
                (1.0, "Second Wind + your E + Doran's Shield win every trade"),
            ]),
        ]),
        Section("Mid/Late Game", [
            Clip(f"{MEDIA}/teamfight.mp4", [
                (1.5, "spit him as far from his tower as possible"),
            ]),
        ]),
    ],
    music=f"{MEDIA}/music.m4a",
)
