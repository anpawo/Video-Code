#!/usr/bin/env python3
"""
Make a folder that runs on another Ubuntu.

    python3 scripts/bundle_linux.py            # → dist/video-code-linux-x86_64/
    python3 scripts/bundle_linux.py --zip      # …and the zip beside it

The macOS twin is scripts/bundle.py, and what to ship is the same list, so it
is imported from there rather than written twice. What differs is the loader:
ELF instead of Mach-O, `ldd` instead of `otool -L`, `patchelf --set-rpath
'$ORIGIN/…'` instead of install_name_tool, and a denylist — glibc, libstdc++,
the X/Wayland/GL/Vulkan stack and the base libraries every Ubuntu already has
must come from the machine that RUNS the folder. Bundling a GPU or GL library
is how a copy renders on the builder and shows a black window everywhere else.

Qt lives outside the system on a build machine (the CI action unpacks it under
the workspace), so its libraries, its plugins and the QML modules the chrome
imports travel too, found through a qt.conf beside the executable.
"""

import argparse
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bundle  # noqa: E402  — the shipping lists, and the smoke test

ROOT = bundle.ROOT
DIST = ROOT / "dist" / f"video-code-linux-{os.uname().machine}"

# What must come from the machine that runs the folder, never from the zip.
# glibc and libstdc++ because a copy of them is how a binary stops loading at
# all; the GL/Vulkan/X/Wayland stack because those libraries are the driver's
# own front door; the rest because every Ubuntu has them and a second copy only
# adds ways to disagree.
SYSTEM = (
    "ld-linux", "libc.so", "libm.so", "libdl.so", "libpthread.so", "librt.so",
    "libutil.so", "libresolv.so", "libnsl.so", "libcrypt.so", "libgcc_s.so",
    "libstdc++.so",
    "libGL", "libEGL", "libGLX", "libGLdispatch", "libOpenGL", "libGLESv2",
    "libgbm", "libdrm", "libvulkan", "libX", "libxcb", "libxkbcommon",
    "libwayland", "libxshmfence",
    "libdbus-1", "libsystemd", "libudev", "libselinux", "libcap",
    "libz.so", "liblzma", "libbz2", "libexpat", "libffi", "libuuid",
    "libssl", "libcrypto", "libglib-2.0", "libgobject", "libgio", "libgmodule",
    "libgthread", "libpcre", "libasound", "libpulse", "libnss", "libmount",
    "libblkid",
)

# The QML modules the chrome imports (QtQml, QtQuick, QtQuick.Controls,
# QtQuick.Window — all of them live under these two directories), minus the
# Controls styles nothing here asks for. `--check-chrome` in a bare container
# is what keeps this pruning honest: every binding resolves, or the build fails.
QML_MODULES = ["QtQml", "QtQuick"]
QML_SKIP = {"Imagine", "Material", "Universal", "iOS", "macOS", "Windows", "Fusion"}

# The plugin folders this application can actually load. Not the whole
# directory: Qt ships a driver for the Mimer database that names a library
# nobody outside Mimer has, and a GTK platform theme that would drag all of
# GTK into the zip. `platforms` is the one that must be here — it holds
# offscreen and xcb.
QT_PLUGINS = ["platforms", "platforminputcontexts", "imageformats", "iconengines",
              "xcbglintegrations", "tls", "wayland-shell-integration",
              "wayland-decoration-client", "wayland-graphics-integration-client"]


def sh(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def is_elf(path: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    with open(path, "rb") as f:
        return f.read(4) == b"\x7fELF"


def is_system(name: str) -> bool:
    return name.startswith(SYSTEM)


def ours(path: Path) -> bool:
    """
    Everything in the bundle except what a wheel brought with it.

    A manylinux wheel ships its own libraries in a sibling `*.libs` directory,
    already patched by auditwheel, and they are NOT loadable one at a time:
    shapely's libgeos_c names libgeos with no rpath of its own, and only
    resolves because the extension module that pulls both in has the rpath.
    `ldd` on one of them alone says "not found" about a wheel that works
    perfectly — so they are left exactly as they came, and what proves them is
    the import in the container.
    """
    return "site-packages" not in path.parts


def deps(elf: Path) -> list[tuple[str, str]]:
    """
    (soname, resolved path) for what this file NAMES; "" when nothing answers.

    `ldd` prints the whole tree, not the file's own list, so everything the
    system's openssl reaches shows up under a Qt plugin that never heard of
    Kerberos. DT_NEEDED is the file's own business and the only thing worth
    rewriting; the rest belongs to whoever named it, and is reached here too
    because every copy is walked in turn.
    """
    own = {line.strip() for line in sh("patchelf", "--print-needed", str(elf)).splitlines() if line.strip()}
    out = []
    for line in sh("ldd", str(elf)).splitlines():
        line = line.strip()
        if "=>" not in line:
            continue  # linux-vdso, and the loader itself
        name, _, rest = line.partition(" => ")
        name = name.strip()
        if name not in own:
            continue
        resolved = rest.rsplit(" (", 1)[0].strip()
        out.append((name, "" if resolved == "not found" else resolved))
    return out


def set_rpath(elf: Path, lib_dir: Path) -> None:
    """Point the file at lib/, keeping the $ORIGIN entries a wheel came with."""
    rel = os.path.relpath(lib_dir, elf.parent)
    ours = "$ORIGIN" if rel == "." else f"$ORIGIN/{rel}"
    old = [p for p in sh("patchelf", "--print-rpath", str(elf)).strip().split(":") if p.startswith("$ORIGIN")]
    sh("patchelf", "--set-rpath", ":".join([ours, *old]), str(elf))


def relocate(lib_dir: Path) -> None:
    """
    Every ELF in the bundle: copy each non-system library it names into lib/,
    then point it there. Repeats until the copies name nothing new.
    """
    seen: set[Path] = set()
    queue = [p for p in DIST.rglob("*") if is_elf(p) and ours(p)]
    while queue:
        elf = queue.pop()
        if elf in seen:
            continue
        seen.add(elf)
        for name, resolved in deps(elf):
            if not resolved and not is_system(name):
                # Qt ships plugins for hardware and databases this machine has
                # never seen. One that cannot be satisfied is dropped rather
                # than shipped broken — Qt skips a plugin it cannot load, and
                # if the dropped one mattered, --check-chrome says so.
                if elf.is_relative_to(lib_dir / "qt"):
                    print(f"dropped {elf.relative_to(DIST)}: needs {name}, absent here")
                    elf.unlink()
                    break
                sys.exit(f"{elf} needs {name}, which is not on this machine")
            if not resolved or is_system(name) or Path(resolved).is_relative_to(DIST):
                continue
            target = lib_dir / name
            if not target.exists():
                shutil.copy2(resolved, target)
                os.chmod(target, 0o755)
                queue.append(target)
        if elf.exists():  # unless it was just dropped
            set_rpath(elf, lib_dir)


def check_clean() -> None:
    """Nothing may resolve to the build machine: that is the whole point."""
    dirty = []
    for elf in (p for p in DIST.rglob("*") if is_elf(p) and ours(p)):
        for name, resolved in deps(elf):
            if not is_system(name) and (not resolved or not Path(resolved).is_relative_to(DIST)):
                dirty.append(f"{elf.relative_to(DIST)} → {resolved or 'nothing'}")
    if dirty:
        sys.exit("still pointing outside the folder:\n  " + "\n  ".join(dirty))


def qt_prefix(binary: Path) -> Path:
    for name, resolved in deps(binary):
        if name.startswith("libQt6Core"):
            return Path(resolved).resolve().parent.parent
    sys.exit("the binary does not link Qt6Core — nothing to take Qt from")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", action="store_true")
    parser.add_argument("--no-smoke", action="store_true")
    args = parser.parse_args()

    binary = ROOT / "video-code"
    if not binary.exists():
        sys.exit("build first: cmake --build build && cp build/video-code .")
    stdlib = Path(sysconfig.get_paths()["stdlib"])
    site = Path(sysconfig.get_paths()["purelib"])

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    lib = DIST / "lib"
    lib.mkdir()

    shutil.copy2(binary, DIST / "video-code")
    os.chmod(DIST / "video-code", 0o755)
    for folder in ("videocode", "assets", "qml"):
        bundle.copy_tree(ROOT / folder, DIST / folder, {"__pycache__", ".DS_Store"})
    (DIST / "scenes").mkdir()
    for scene in bundle.SCENES:
        shutil.copy2(scene, DIST / "scenes" / scene.name)
    (DIST / "test").mkdir()
    for wav in ("test.wav", "test_speech.wav"):
        shutil.copy2(ROOT / "test" / wav, DIST / "test" / wav)
    (DIST / "test" / "visual" / "scenes").mkdir(parents=True)
    for name in ("shapes", "camera", "composition"):
        shutil.copy2(ROOT / "test" / "visual" / "scenes" / f"{name}.py", DIST / "test" / "visual" / "scenes" / f"{name}.py")

    # Python: the interpreter's library, the stdlib, the packages. Main.cpp
    # sets PYTHONHOME to python/ when python/lib exists, so the layout is the
    # same as the macOS bundle's.
    dest = DIST / "python" / "lib" / stdlib.name
    bundle.copy_tree(stdlib, dest, bundle.STDLIB_SKIP)
    # _tkinter goes with the tkinter package STDLIB_SKIP already leaves behind:
    # the module without its package imports nothing, and it is the one thing
    # in the stdlib that names a windowing toolkit.
    for so in (list((dest / "lib-dynload").glob("_test*"))
               + list((dest / "lib-dynload").glob("xx*"))
               + list((dest / "lib-dynload").glob("_tkinter*"))):
        so.unlink()
    for config in dest.glob("config-*"):  # the static library and the makefiles a build needs, 10 MB
        shutil.rmtree(config)
    (dest / "site-packages").mkdir()
    for name in bundle.SITE:
        src = site / name
        if src.is_dir():
            bundle.copy_tree(src, dest / "site-packages" / name, {"__pycache__", "tests", "test"})
        else:
            shutil.copy2(src, dest / "site-packages" / name)
    # A manylinux wheel keeps its own shared libraries in a sibling directory
    # and reaches them by an $ORIGIN rpath — copy the package without it and
    # numpy imports into an ImportError.
    for extra in site.glob("*.libs"):
        if extra.name.split(".")[0].lower() in {n.lower() for n in bundle.SITE_INFO}:
            bundle.copy_tree(extra, dest / "site-packages" / extra.name)
    for info in site.glob("*.dist-info"):
        if any(info.name.lower().startswith(p + "-") for p in bundle.SITE_INFO):
            bundle.copy_tree(info, dest / "site-packages" / info.name)

    # Qt: the plugins (the offscreen and xcb platforms live here) and the QML
    # modules the chrome imports. qt.conf is how the copy finds them without a
    # launcher script or an environment variable.
    prefix = qt_prefix(binary)
    qt = lib / "qt"
    for folder in QT_PLUGINS:
        if (prefix / "plugins" / folder).is_dir():
            bundle.copy_tree(prefix / "plugins" / folder, qt / "plugins" / folder)
    (qt / "qml").mkdir(parents=True)
    for module in QML_MODULES:
        bundle.copy_tree(prefix / "qml" / module, qt / "qml" / module, QML_SKIP)
    (DIST / "qt.conf").write_text("[Paths]\nPrefix = .\nLibraries = lib\nPlugins = lib/qt/plugins\nQml2Imports = lib/qt/qml\n")

    # relocate() would pick libpython up from the binary's own list, but only
    # if the loader can still find it — a Python outside /usr is exactly the
    # case that fails. Copy it by name first, under its soname.
    libdir = Path(sysconfig.get_config_var("LIBDIR") or "/usr/lib")
    versioned = sorted(p for p in libdir.glob("libpython3.*.so.*") if not p.is_symlink())
    for dylib in versioned[:1]:
        shutil.copy2(dylib, lib / dylib.name)
        os.chmod(lib / dylib.name, 0o755)

    relocate(lib)
    check_clean()

    (DIST / "README.txt").write_text(README)
    size = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file()) // 1_000_000
    print(f"bundle: {DIST} ({size} MB), nothing left pointing outside it")

    if not args.no_smoke:
        bundle.smoke(DIST)
    if args.zip:
        archive = shutil.make_archive(str(DIST), "zip", DIST.parent, DIST.name)
        print(f"zip: {archive} ({Path(archive).stat().st_size // 1_000_000} MB)")


README = """Video-Code — a folder that runs
================================

Needs: Ubuntu 24.04 or newer (x86_64), and three packages from apt:

    sudo apt install ffmpeg mesa-vulkan-drivers libvulkan1

Nothing else: Python, its packages and Qt are inside. The renderer draws with
Vulkan — mesa-vulkan-drivers is what makes it work on a machine with no GPU
driver of its own.

  1. cd into this folder
  2. ./video-code --file scenes/first_rectangle.py --generate smoke.mp4

If smoke.mp4 plays a blue rectangle fading in, everything works.

  ./video-code --file scenes/tour.py --generate tour.mp4      # 31 s, six chapters, sound
  ./video-code --file scenes/tour.py --generate look.png --from 2.5
  ./video-code --file scenes/tour.py --generate sheet.png --sheet 4 --from 0 --to 12
  ./video-code --file scenes/tour.py --generate tour.mp4 --for youtube,tiktok,square
  ./video-code --file scenes/tour.py --inspect                 # the timeline as JSON
  ./video-code --file scenes/tour.py --editor                  # the editor window
  ./video-code tell state                                       # ask the open editor where you are

The editor needs a desktop session (X11 or Wayland). Everything above it
renders without one.

What is here
  video-code    the engine and the editor
  videocode/    the Python library a scene imports
  scenes/       the example scenes, one feature each
  assets/ qml/  fonts, shaders and the editor chrome
  python/ lib/  a private Python and Qt — not yours, not touched
  test/         two short sounds for the sound scene

The scenes are ordinary Python files. Read one before you run it, the way you
would any script someone sent you.
"""

if __name__ == "__main__":
    main()
