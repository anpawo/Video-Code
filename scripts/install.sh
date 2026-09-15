#!/bin/sh
# Fetches the latest Video-Code release for this machine into a folder and renders one scene.
#   curl -fsSL https://raw.githubusercontent.com/anpawo/Video-Code/main/scripts/install.sh | sh
#   sh scripts/install.sh [folder]        # default: ./video-code
set -eu

case "$(uname -s)-$(uname -m)" in
    Darwin-arm64) name=video-code-macos-arm64 ;;
    Linux-x86_64) name=video-code-linux-x86_64 ;;
    *) echo "no prebuilt Video-Code for $(uname -s) $(uname -m) - build it: docs/user/user.md" >&2; exit 1 ;;
esac

# bsdtar on macOS reads xz by itself; GNU tar on Linux calls the xz binary.
[ "$(uname -s)" = Darwin ] || command -v xz >/dev/null || { echo "xz is missing (sudo apt install xz-utils)" >&2; exit 1; }
command -v ffmpeg >/dev/null || {
    echo "ffmpeg is missing." >&2
    echo "  macOS:  brew install ffmpeg" >&2
    echo "  Ubuntu: sudo apt install ffmpeg mesa-vulkan-drivers libvulkan1 libopengl0 libegl1 libglx0 libxkbcommon0 libopencv-imgcodecs406t64 libopencv-videoio406t64" >&2
    exit 1
}

dir=${1:-./video-code}
[ ! -e "$dir" ] || { echo "$dir already exists - remove it or pass another folder" >&2; exit 1; }

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fL --progress-bar "https://github.com/anpawo/Video-Code/releases/latest/download/$name.tar.xz" -o "$tmp/$name.tar.xz"
tar -xJf "$tmp/$name.tar.xz" -C "$tmp"
mv "$tmp/$name" "$dir"
[ "$(uname -s)" != Darwin ] || xattr -dr com.apple.quarantine "$dir"   # not notarised

"$dir/video-code" --file "$dir/scenes/first_rectangle.py" --generate "$dir/smoke.mp4"
echo
echo "Video-Code is in $dir - smoke.mp4 there is a blue rectangle fading in. Next:"
echo "  $dir/video-code --file $dir/scenes/tour.py --generate tour.mp4"
echo "  $dir/video-code --file $dir/scenes/tour.py --editor"
