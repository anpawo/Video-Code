#!/usr/bin/env python3

#
# chess_montage.py — le montage de la partie d'echecs, en deux bobines.
#
# Bobine 1 (ici) : la PRESENTATION DES EFFETS. Chaque plan ne joue qu'un seul
# effet et ecrit son nom a l'ecran, pour qu'ensuite "mets-moi un snapZoom la"
# veuille dire quelque chose de precis.
#
# Bobine 2 (a venir) : le montage de la partie elle-meme, qui piochera dans le
# vocabulaire nomme ci-dessous.
#
#   # ouvrir dans l'UI (dock, timeline, proprietes) :
#   MONTAGE_SOURCE=~/Desktop/Projets/Evolvia/first_test.mov \
#   ./video-code --editor --file chess_montage.py
#
#   # sortir le fichier, a la taille et au fps de la source :
#   MONTAGE_SOURCE=~/Desktop/Projets/Evolvia/first_test.mov \
#   ./video-code --file chess_montage.py --generate reel.mp4 \
#                --width 1322 --height 1526 --framerate 60
#
# --width/--height sont LIBRES : le plan est mis a l'echelle pour TENIR dans le
# cadre (jamais deforme, jamais recadre), et ce qui reste est noir. Les donner
# a la taille native de la source evite un reechantillonnage inutile.
#
# --framerate ne fait que le fichier de sortie : une scene est TOUJOURS ecrite
# a 30 fps (Config::SCENE_FRAMERATE, en dur dans le C++), et le compilateur
# duplique ou jette des images pour atteindre le fps demande. Un rendu a 60
# donne donc un fichier a 60 fps, avec 30 images distinctes par seconde. La
# vitesse de LECTURE de la source, elle, est reglee par la rampe plus bas.
#
# Toutes les coordonnees sont des FRACTIONS, jamais des pixels et jamais quoi
# que ce soit qui sache ce qui est filme :
#   - les mouvements de camera (zoomTo, travelling, impact, whipPan) prennent
#     des fractions de la boite du MEDIA ;
#   - la lumiere (spotlightOn, zoneFocus) prend des fractions du CADRE.
# Traduire "la case c5" en l'un des deux, c'est le boulot de l'appelant —
# videocode ne connait pas les echecs, et c'est voulu.
#

import os
import subprocess

from videocode import *
# Les effets de montage vivent dans effect/other/ : ce ne sont pas des
# methodes d'Input, on les importe un par un et on les passe a .apply().
from videocode.template.effect.other.camera import punchIn, snapZoom, travelling, zoomTo
from videocode.template.effect.other.desaturate import desaturate
from videocode.template.effect.other.flash import flash
from videocode.template.effect.other.glitchBurst import glitchBurst
from videocode.template.effect.other.impact import impact
from videocode.template.effect.other.scope import scope, unscope
from videocode.template.effect.other.spotlightOn import spotlightOn, zoneFocus
from videocode.template.effect.other.vignetteIn import vignetteBeat
from videocode.template.effect.other.whipPan import whipPan
from videocode.template.input._inputs import *

# La source est une variable d'environnement pour que le fichier reste valable
# quand la video change de nom ou de dossier.
SOURCE = os.path.expanduser(os.environ.get("MONTAGE_SOURCE", "~/Desktop/Projets/Evolvia/first_test.mov"))

SHOT = 2.6              # secondes par plan : assez pour lire l'etiquette, assez court pour couper
LEAD = 0.5              # retard a l'allumage : la plaque est montee (0.15 + 0.3) avant que l'effet parte
TAIL = 0.4              # queue en fin de plan : laisse la place au recadrage avant la coupe
EFFECT = SHOT - LEAD - TAIL   # duree max d'un effet, pour qu'il tienne dans son plan
START_AT = 19.0         # on entre dans la partie a 19 s, la ou il se passe quelque chose

PLATE = rgba(28, 30, 40, 235)   # fond de la plaque de titre (opaque : sinon les pieces transparaissent)
ACCENT = rgba(255, 168, 150)    # le nom de l'effet
MUTED = rgba(150, 162, 200)     # la ligne de description

# Le point sur lequel on revient : le centre du plateau dans CETTE capture.
# Une fraction, mesuree une fois a l'oeil — on donne un nombre a videocode,
# pas un nom de case.
FOCUS_X, FOCUS_Y = 0.5, 0.52


def probeSource() -> tuple[float, float, float]:
    """Largeur, hauteur et images/seconde de la source, lues une seule fois."""
    # On lit la vraie taille plutot que de la coder en dur, sinon changer de
    # source casse le cadrage en silence.
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate", "-of", "csv=p=0", SOURCE],
        capture_output=True, text=True, check=True,
    )
    width, height, rate = out.stdout.strip().split(",")[:3]
    num, _, den = rate.partition("/")          # ffprobe rend le fps en fraction exacte
    return float(width), float(height), float(num) / float(den or 1)


def containSize(sourceWidth: float, sourceHeight: float) -> tuple[float, float]:
    """
    Taille du media, en unites monde, qui TIENT dans le cadre sans deformer.

    min() = "contain" : l'image entiere est visible, et s'il reste de la place
    sur un cote elle est noire (voir `backdrop`). max() ferait "cover", qui
    remplit le cadre mais RECADRE — on perdait des bouts du plateau des que le
    ratio de sortie ne collait pas exactement a celui de la source.
    """
    factor = min(WORLD_WIDTH / sourceWidth, WORLD_HEIGHT / sourceHeight)
    return sourceWidth * factor, sourceHeight * factor


# Largeur utile : on garde une marge de chaque cote, sinon la plaque touche le
# bord du cadre et les descriptions longues sortent de l'image.
MARGIN = 0.5
USABLE = WORLD_WIDTH - 2 * MARGIN

# DEFAUT MESURE DE LA LIBRAIRIE : Text.width sous-estime la largeur rendue.
# Mesure faite a 936x1080, fontSize 0.3, police par defaut : la chaine
# "poussee lente, la camera n'est jamais fixe" annonce 5.79 unites monde et en
# occupe ~8.0 a l'ecran (un Rectangle de width=t.width pose derriere le texte
# ne couvre que le milieu de la phrase). Le rapport est stable d'une chaine a
# l'autre, donc on corrige par ce facteur au lieu de se fier a la valeur brute.
# A retirer le jour ou Text.width sera juste — d'ou la constante nommee plutot
# qu'un 1.4 dissemine dans le code.
TEXT_ADVANCE = 1.4


def drawnWidth(text: Text) -> number:
    """Largeur reellement occupee a l'ecran — voir TEXT_ADVANCE."""
    return text.width * TEXT_ADVANCE


def title(name: str, description: str, at: sec) -> None:
    """La plaque de nom — la raison d'etre de la bobine."""
    label = Text(name, fontSize=0.5, fillColor=ACCENT, bold=True)
    # Il faut un Text pour mesurer un Text — mais un Text fabrique puis jete
    # ne disparait pas : il reste dans la scene et se dessine a l'origine
    # (defaut X8, docs/by-example/features/shots.py), ce qui laissait une ligne
    # fantome en travers de toutes les images. On mesure donc sur une taille de
    # reference, puis on cache le metre POUR DE BON — lettre par lettre, la
    # seule facon de masquer un Text (voir le commentaire du gating plus bas).
    RULER = 0.3
    gauge = Text(description, fontSize=RULER, fillColor=MUTED)
    ruler = drawnWidth(gauge)
    for letter in gauge.inputs:
        letter.hide()
    sub = Text(
        description,
        fontSize=RULER * min(1.0, USABLE / ruler),
        fillColor=MUTED,
    )
    # La plaque se dimensionne sur le texte le plus large : une largeur fixe
    # couperait les descriptions longues.
    plate = Rectangle(
        width=min(max(drawnWidth(label), drawnWidth(sub)) + 0.6, WORLD_WIDTH - 0.3),
        height=1.4,
        fillColor=PLATE,
        strokeColor=TRANSPARENT,
        cornerRadius=12,
    )
    # WORLD_HEIGHT/2 est le haut du cadre, donc -WORLD_HEIGHT/2 + 1.5 pose la
    # plaque en bas avec une marge (l'axe y monte, comme en maths).
    y = -WORLD_HEIGHT / 2 + 1.5
    plate.position(0, y).zIndex(10)
    label.position(0, y + 0.28).zIndex(11)
    sub.position(0, y - 0.32).zIndex(11)
    for part in (plate, label, sub):
        # Cacher AVANT, sinon les 13 plaques sont toutes a l'ecran des la frame 0.
        #
        # Et il faut cacher ce qui est REELLEMENT DESSINE : un Text n'est pas un
        # input pose, c'est un Group de Letter (`composite is True`), et seules
        # ses lettres arrivent au rendu. Mesure faite : sur un Text, ni
        # `opacity(0)`, ni `hide()` sur le groupe, ni le garage hors-cadre ne
        # tiennent avant le premier fadeIn — seul `hide()` pose sur chaque
        # lettre tient. Sur un Rectangle, `composite is False` et la liste se
        # reduit a l'element lui-meme : le meme code marche pour les deux.
        for drawn in (part.inputs if part.composite else [part]):
            drawn.hide()
            drawn.show(at=at + 0.15)
        # at= est l'horloge du FILM ; start= serait l'horloge de l'element,
        # donc cumulatif — c'est exactement le piege qui empilait les plans.
        # Une frame apres le show : on ne peut pas faire monter l'opacite d'un
        # input encore cache.
        part.fadeIn(at=at + 0.15 + SINGLE_FRAME, duration=0.3)
        # fadeOut ne relaie pas at= jusqu'a apply() : on avance la montre de
        # l'element a la main, puis on sort en start=0 (= "maintenant").
        part.waitTo(round((at + SHOT - TAIL) * FRAMERATE))
        # hide=True : une fois invisible, l'input sort vraiment du rendu.
        part.fadeOut(duration=0.3, hide=True)


# --- la bobine --------------------------------------------------------------
# (nom, description d'une ligne, l'effet, faut-il recadrer apres le plan)

shots: list[tuple[str, str, Effect, bool]] = [
    # zoom lent et continu : ne touche QUE scale, donc il se combinerait avec
    # un panoramique sans se marcher dessus.
    ("punchIn", "poussee lente, la camera n'est jamais fixe",
     punchIn(zoom=1.22, duration=EFFECT), True),
    # le zoom est pose une fois sur la premiere frame, ensuite c'est un pur
    # deplacement : d'un coin a l'autre du media.
    ("travelling", "glissement d'un point a un autre, zoom fixe",
     travelling(fromX=0.15, fromY=0.8, toX=0.85, toY=0.2, zoom=1.7, duration=EFFECT), True),
    # zoomTo recadre pour amener (x, y) au centre du cadre, et y reste.
    ("zoomTo", "on pousse sur un point precis et on y reste",
     zoomTo(x=FOCUS_X, y=FOCUS_Y, zoom=2.2, duration=1.2), True),
    # aller-retour : attaque exponentielle, palier, retour exact a l'origine —
    # d'ou needsReframe=False, il se remet en place tout seul.
    ("snapZoom", "on saute sur le point, on tient, on revient",
     snapZoom(x=FOCUS_X, y=FOCUS_Y, zoom=2.4, hold=EFFECT - 0.9), False),
    # punch + secousse amortie dans UN SEUL effet : deux effets separes se
    # battraient pour le canal position et le dernier ecraserait l'autre.
    ("impact", "le coup : punch + secousse amortie",
     impact(x=FOCUS_X, y=FOCUS_Y, zoom=1.3, amplitude=0.14, duration=0.9), False),
    # DEGRADE assume : un vrai whip file dans le sens du mouvement, le blur de
    # videocode est isotrope (pas de shader de flou directionnel). A 0.4 s ca
    # passe pour un fouette ; plus lent, ca se voit.
    ("whipPan", "fouette d'un point a l'autre, flou dans le mouvement",
     whipPan(toX=0.85, toY=0.35, blur=12, duration=0.4), True),
    # spotlight : coordonnees du CADRE, pas du media (c'est un shader, il
    # travaille sur les pixels rendus et ignore la geometrie du plan).
    ("spotlightOn", "tout s'assombrit sauf une flaque de lumiere",
     spotlightOn(x=0.5, y=0.5, radius=0.17, duration=EFFECT), False),
    ("zoneFocus", "meme chose, mais sur une zone rectangulaire",
     zoneFocus(x=0.5, y=0.45, width=0.62, height=0.5, duration=EFFECT), False),
    ("desaturate", "la couleur se vide puis revient",
     desaturate(amount=1.0, duration=EFFECT, fade=0.5), False),
    ("flash", "le blanc qui claque",
     flash(amount=170, times=2, duration=0.9), False),
    # glitch est pilote par le temps : on en emet UN avec une duree. En emettre
    # un par frame relancerait son horloge a chaque frame et le motif figerait.
    ("glitchBurst", "coupure de signal : tranches et blocs",
     glitchBurst(amount=6, blocks=30, duration=0.5), False),
    ("vignetteBeat", "les coins se ferment et se rouvrent",
     vignetteBeat(intensity=0.75, duration=EFFECT), False),
    ("scope", "bandes cinema, 2.39:1",
     scope(ratio=2.39, duration=0.6), False),
]

REEL = len(shots) * SHOT  # duree totale visee, en secondes de film

sourceWidth, sourceHeight, sourceFps = probeSource()
clipWidth, clipHeight = containSize(sourceWidth, sourceHeight)

# Les bandes. En "contain", ce qui n'est pas couvert par le plan reste
# transparent : on pose un fond noir plein cadre dessous pour que ce soit des
# BANDES NOIRES et pas un trou. zIndex(-1) : sous tout le reste.
backdrop = Rectangle(
    width=WORLD_WIDTH, height=WORLD_HEIGHT,
    fillColor=BLACK, strokeColor=TRANSPARENT,
)
backdrop.position(0, 0).zIndex(-1)

# LA VITESSE DE LECTURE — le piege le moins evident de ce moteur.
#
# Le moteur consomme UNE frame source par frame de SCENE, et une scene est
# toujours ecrite a 30 fps (`Config::SCENE_FRAMERATE`, en dur cote C++ ;
# --framerate ne change que le fichier de sortie, en dupliquant des images).
# Une source a 60 fps jouait donc a DEMI-VITESSE : tout etait au ralenti.
#
# On ne peut pas corriger ca avec `speedRamps` : une rampe change bien quelle
# frame source est decodee, mais la longueur que le clip revendique reste
# `endFrame - startFrame`, sans tenir compte du taux — la bobine sortait deux
# fois trop longue, avec une queue muette apres le dernier plan. Seuls les
# `cuts` reduisent cette longueur.
#
# Ce qui tombe bien, parce que passer de 60 a 30 fps, c'est litteralement
# jeter une image sur deux. `decimate` le fait, pour un rapport quelconque.


def decimate(first: int, frames: int, ratio: float) -> list[tuple[int, int]]:
    """
    Les `cuts` qui ne gardent qu'une frame source sur `ratio`.

    `frames` est le nombre de frames de SCENE voulues ; la frame de scene i
    prend la frame source `first + round(i * ratio)`, et tout le reste de la
    fenetre est coupe. Avec ratio=2.0 c'est une image sur deux ; avec 1.0 la
    liste est vide et rien n'est coupe.
    """
    kept = {first + round(i * ratio) for i in range(frames)}
    spans: list[tuple[int, int]] = []
    f = first
    last = first + round((frames - 1) * ratio) + 1
    while f < last:
        if f in kept:
            f += 1
            continue
        gap = f
        while f < last and f not in kept:
            f += 1
        spans.append((gap, f))
    return spans


# startFrame / endFrame sont en frames SOURCE, au fps de la source. La fenetre
# doit donc couvrir REEL secondes de SOURCE, que la decimation ramene ensuite a
# REEL secondes de scene. Sans endFrame, le clip reclamerait toute sa duree
# (ici 10 min de rendu).
sceneFrames = round(REEL * FRAMERATE)
ratio = sourceFps / FRAMERATE          # 2.0 pour une source a 60 fps, 1.0 a 30
firstFrame = int(START_AT * sourceFps)
clip = Video(
    SOURCE,
    startFrame=firstFrame,
    endFrame=firstFrame + round((sceneFrames - 1) * ratio) + 1,
    cuts=decimate(firstFrame, sceneFrames, ratio),
    width=clipWidth,
    height=clipHeight,
)
# zIndex(0) : le plan est le fond, les plaques de titre passeront au-dessus.
clip.position(0, 0).zIndex(0)


def reframe(at: sec) -> None:
    """
    Remet le plan a son cadrage d'origine. zoomTo / travelling / punchIn sont
    A ETAT : ils laissent la camera la ou ils l'ont amenee. Une bobine qui les
    enchaine doit donc le dire explicitement, sinon chaque effet demarre du
    cadrage du precedent et ca part en vrille.
    """
    clip.apply(position(0, 0), scale(1, 1), at=at)


for index, (name, description, effect, needsReframe) in enumerate(shots):
    at = index * SHOT              # chaque plan demarre a son rang * SHOT
    title(name, description, at)
    # at= (horloge du film) et non start= (horloge de l'element, cumulative).
    # at + LEAD, pas at : les effets brefs (flash, glitchBurst, scope) etaient
    # finis avant que leur propre etiquette soit lisible — dans une bobine dont
    # le seul but est de NOMMER les effets, c'est le defaut le plus couteux.
    clip.apply(effect, at=at + LEAD)
    if needsReframe:
        # Le recadrage se pose dans la queue du plan : apres la fin de l'effet
        # (qui dure au plus EFFECT) et avant le plan suivant. at= refuse
        # d'ecrire dans le passe de l'element, d'ou cet ordre strict.
        reframe(at + SHOT - 0.15)

# scope est le seul look qui doit etre defait a la main : les bandes restent.
# On le defait apres la fin de scope, sinon les deux ecritures se disputent le
# canal Crop sur les memes frames (le moteur le signale, et la derniere gagne).
clip.apply(unscope(ratio=2.39, duration=0.5), at=(len(shots) - 1) * SHOT + LEAD + 0.8)

# --- retiming ---------------------------------------------------------------
# ralenti / accelere / freezeFrame / rewind ne sont PAS des effets : ils
# changent quelle frame SOURCE est decodee, ce que Video decide une fois pour
# toutes a la construction. Voir videocode/template/effect/other/retime.py.
# La bobine ci-dessus ne peut pas les montrer sans reconstruire le clip, donc
# ils se jouent sur une passe a part :
#
#   Video(SOURCE, speedRamps=[
#       *ralenti(at=2, duration=3, rate=0.35),
#       *accelere(at=8, duration=20, rate=6),
#       *freezeFrame(at=30, duration=1.5),
#   ])
#
# L'echantillonnage est a la frame la plus proche, sans interpolation : le
# ralenti est un vrai ralenti, pas un ralenti fluidifie facon optical flow —
# ca n'existe pas dans le moteur.
