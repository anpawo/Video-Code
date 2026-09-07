#!/usr/bin/env python3
"""
Make a folder that runs on another Mac.

    python3 scripts/bundle.py            # → dist/video-code-macos-arm64/
    python3 scripts/bundle.py --zip      # …and dist/video-code-macos-arm64.zip

The built binary points at this machine: libpython from pyenv, MoltenVK from
Homebrew, shaders and QML in the checkout, the stdlib where pyenv keeps it.
A copy on a tester's Mac died on its first line. This script copies each of
those next to the executable, rewrites every Mach-O reference to a path
relative to the file that holds it, and checks with otool that nothing under
/Users or /opt/homebrew is left. The binary itself finds `python/`, `qml/` and
`assets/` beside it (utils/Paths.hpp, Main.cpp), so no launcher script is
needed: unpack, run.

Then it runs the copy from somewhere else, without the environment, and
renders a scene: the check that matters.
"""

import argparse
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "video-code-macos-arm64"
FOREIGN = ("/Users/", "/opt/homebrew/", "/usr/local/")

# The Python packages a scene can reach. basedpyright, cv2 and faster-whisper
# are left out: the first is the editor's language server (72 MB, pip installs
# it), the others are optional and say so in requirements.txt.
SITE = ["shapely", "numpy", "PIL", "freetype", "uharfbuzz", "pygments", "svgelements", "typing_extensions.py"]
SITE_INFO = ["shapely", "numpy", "pillow", "freetype_py", "uharfbuzz", "pygments", "svgelements", "typing_extensions"]
# What the stdlib carries that no scene needs: 150 MB of tests, an IDE, Tk.
STDLIB_SKIP = {"site-packages", "test", "tests", "idlelib", "tkinter", "turtledemo", "ensurepip", "__pycache__", "config-3.14-darwin", "lib2to3", "pydoc_data"}

# The Acceptance Test Plan's own scenes — its 24 tests name these files and
# describe what they show, so they ship as written — plus the tour.
SCENES = [*sorted((ROOT / "docs" / "atp" / "scenes").glob("*.py")), ROOT / "docs" / "by-example" / "tour.py"]


def sh(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def own_id(macho: Path) -> str:
    # Header lines ("path:", "path (architecture arm64):") end with a colon;
    # the id, when the file has one, is the line that does not.
    ids = [line.strip() for line in sh("otool", "-D", str(macho)).splitlines() if line.strip() and not line.rstrip().endswith(":")]
    return ids[0] if ids else ""


def deps(macho: Path) -> list[str]:
    """What the file loads: the tab-indented lines, its own install name left out."""
    me = own_id(macho)
    out = sh("otool", "-L", str(macho)).splitlines()
    return [line.split()[0] for line in out if line.startswith("\t") and line.split()[0] != me]


def is_macho(path: Path) -> bool:
    if path.suffix in (".dylib", ".so"):
        return True
    if path.suffix or not path.is_file():
        return False
    with open(path, "rb") as f:
        return f.read(4) in (b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe")


def copy_tree(src: Path, dst: Path, skip: set[str] | frozenset[str] = frozenset()) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        return {n for n in names if n in skip or n.endswith(".pyc")}

    shutil.copytree(src, dst, ignore=ignore, symlinks=False)


def relocate(bundle: Path, lib_dir: Path) -> None:
    """
    Every Mach-O in the bundle: copy each foreign dylib it names into lib_dir
    and point the reference at it, relative to the file. Repeats until the
    copies themselves name nothing foreign.
    """
    seen: set[Path] = set()
    queue = [p for p in bundle.rglob("*") if p.is_file() and is_macho(p)]
    while queue:
        macho = queue.pop()
        if macho in seen:
            continue
        seen.add(macho)
        changed = False
        # A wheel's own dylib carries the absolute id of the machine it was
        # installed on; nothing loads it by that name, but a clean bundle
        # should not spell this machine anywhere.
        if own_id(macho).startswith(FOREIGN):
            sh("install_name_tool", "-id", f"@rpath/{macho.name}", str(macho))
            changed = True
        for dep in deps(macho):
            if not dep.startswith(FOREIGN):
                continue
            name = Path(dep).name
            target = lib_dir / name
            if not target.exists():
                if not Path(dep).exists():
                    sys.exit(f"{macho} names {dep}, which is not on this machine")
                shutil.copy2(dep, target)
                os.chmod(target, 0o755)
                sh("install_name_tool", "-id", f"@rpath/{name}", str(target))
                queue.append(target)
            rel = os.path.relpath(target, macho.parent)
            sh("install_name_tool", "-change", dep, f"@loader_path/{rel}", str(macho))
            changed = True
        if changed:
            # install_name_tool breaks the signature; an ad-hoc one is enough
            # for a binary that was never notarised anyway.
            sh("codesign", "-f", "-s", "-", str(macho))


def check_clean(bundle: Path) -> None:
    dirty = []
    for macho in (p for p in bundle.rglob("*") if p.is_file() and is_macho(p)):
        for dep in deps(macho) + [own_id(macho)]:
            if dep.startswith(FOREIGN):
                dirty.append(f"{macho.relative_to(bundle)} → {dep}")
    if dirty:
        sys.exit("still pointing at this machine:\n  " + "\n  ".join(dirty))


def smoke(bundle: Path) -> None:
    """Run the copy from elsewhere, with an empty environment, and render."""
    with tempfile.TemporaryDirectory() as tmp:
        elsewhere = Path(tmp) / "unpacked"
        shutil.copytree(bundle, elsewhere, symlinks=True)
        env = {"PATH": "/usr/bin:/bin:/opt/homebrew/bin", "HOME": tmp}
        probe = Path(tmp) / "probe.py"
        probe.write_text("import sys, shapely, PIL, freetype, uharfbuzz\nfrom videocode import *\nprint('PYTHONPREFIX', sys.prefix)\nSquare(side=1)\n")
        out = subprocess.run([str(elsewhere / "video-code"), "--file", str(probe), "--inspect"], cwd=tmp, env=env, capture_output=True, text=True, timeout=120)
        if out.returncode != 0:
            sys.exit(f"the copy could not run a scene:\n{out.stdout}\n{out.stderr}")
        if str(elsewhere) not in out.stdout and "PYTHONPREFIX " + str(elsewhere) not in out.stdout + out.stderr:
            print("note: sys.prefix was not printed by --inspect; checked import only")
        film = Path(tmp) / "smoke.mp4"
        out = subprocess.run(
            [str(elsewhere / "video-code"), "--file", str(elsewhere / "scenes" / "tour.py"), "--generate", str(film), "--to", "3"],
            cwd=elsewhere, env=env, capture_output=True, text=True, timeout=600,
        )
        if out.returncode != 0 or not film.exists() or film.stat().st_size < 10_000:
            sys.exit(f"the copy could not render tour.py:\n{out.stdout[-2000:]}\n{out.stderr[-2000:]}")
        print(f"smoke: {film.stat().st_size // 1000} kB rendered from a copy in {elsewhere}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", action="store_true")
    parser.add_argument("--no-smoke", action="store_true")
    args = parser.parse_args()

    binary = ROOT / "video-code"
    if not binary.exists():
        sys.exit("build first: make")
    py_home = Path(sysconfig.get_paths()["stdlib"]).parent.parent  # …/3.14.2
    stdlib = Path(sysconfig.get_paths()["stdlib"])                  # …/lib/python3.14
    site = Path(sysconfig.get_paths()["purelib"])

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    lib = DIST / "lib"
    lib.mkdir()

    shutil.copy2(binary, DIST / "video-code")
    for folder in ("videocode", "assets", "qml"):
        copy_tree(ROOT / folder, DIST / folder, {"__pycache__", ".DS_Store"})
    (DIST / "scenes").mkdir()
    for scene in SCENES:
        shutil.copy2(scene, DIST / "scenes" / scene.name)
    (DIST / "test").mkdir()
    for wav in ("test.wav", "test_speech.wav"):
        shutil.copy2(ROOT / "test" / wav, DIST / "test" / wav)
    # `--check-widget` (the plan's F24) drives three scenes of the visual suite
    # through both renderers — kParityCases in VisualTest.cpp names them by
    # this path.
    (DIST / "test" / "visual" / "scenes").mkdir(parents=True)
    for name in ("shapes", "camera", "composition"):
        shutil.copy2(ROOT / "test" / "visual" / "scenes" / f"{name}.py", DIST / "test" / "visual" / "scenes" / f"{name}.py")

    # Python: the interpreter's library, the stdlib, the packages.
    dylib = py_home / "lib" / "libpython3.14.dylib"
    shutil.copy2(dylib, lib / dylib.name)
    os.chmod(lib / dylib.name, 0o755)
    sh("install_name_tool", "-id", f"@rpath/{dylib.name}", str(lib / dylib.name))
    dest = DIST / "python" / "lib" / stdlib.name
    copy_tree(stdlib, dest, STDLIB_SKIP)
    for so in list((dest / "lib-dynload").glob("_test*")) + list((dest / "lib-dynload").glob("xx*")):
        so.unlink()
    (dest / "site-packages").mkdir()
    for name in SITE:
        src = site / name
        if src.is_dir():
            copy_tree(src, dest / "site-packages" / name, {"__pycache__", "tests", "test"})
        else:
            shutil.copy2(src, dest / "site-packages" / name)
    for info in site.glob("*.dist-info"):
        if any(info.name.lower().startswith(p + "-") for p in SITE_INFO):
            copy_tree(info, dest / "site-packages" / info.name)

    # The executable's own references first, by name, so the rewrite is exact.
    for dep in deps(DIST / "video-code"):
        if dep.endswith("libpython3.14.dylib"):
            sh("install_name_tool", "-change", dep, "@executable_path/lib/libpython3.14.dylib", str(DIST / "video-code"))
    relocate(DIST, lib)
    sh("codesign", "-f", "-s", "-", str(DIST / "video-code"))
    check_clean(DIST)

    (DIST / "README.txt").write_text(README)
    size = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file()) // 1_000_000
    print(f"bundle: {DIST} ({size} MB), no reference to this machine left")

    if not args.no_smoke:
        smoke(DIST)
    if args.zip:
        archive = shutil.make_archive(str(DIST), "zip", DIST.parent, DIST.name)
        print(f"zip: {archive} ({Path(archive).stat().st_size // 1_000_000} MB)")


README = """Video-Code — a folder that runs
================================

Needs: a Mac with Apple Silicon, macOS 14 or newer, and ffmpeg on the PATH
(`brew install ffmpeg`). Nothing else: Python and its packages are inside.

  1. cd into this folder
  2. xattr -dr com.apple.quarantine .        # it is not notarised
  3. ./video-code --file scenes/first_rectangle.py --generate smoke.mp4

If smoke.mp4 plays a blue rectangle fading in, everything works.

  ./video-code --file scenes/tour.py --generate tour.mp4      # 31 s, six chapters, sound
  ./video-code --file scenes/tour.py --generate look.png --from 2.5
  ./video-code --file scenes/tour.py --generate sheet.png --sheet 4 --from 0 --to 12
  ./video-code --file scenes/tour.py --generate tour.mp4 --for youtube,tiktok,square
  ./video-code --file scenes/tour.py --inspect                 # the timeline as JSON
  ./video-code --file scenes/tour.py --editor                  # the editor window
  ./video-code tell state                                       # ask the open editor where you are

What is here
  video-code    the engine and the editor
  videocode/    the Python library a scene imports
  scenes/       the example scenes, one feature each
  assets/ qml/  fonts, shaders and the editor chrome
  python/ lib/  a private Python 3.14 with its packages — not yours, not touched
  test/         two short sounds for the sound scene

The scenes are ordinary Python files. Read one before you run it, the way you
would any script someone sent you.
"""

if __name__ == "__main__":
    main()
