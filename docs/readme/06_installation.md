### Installation

The quickest way is a prebuilt folder — no compiler, no Qt, no Python to install:

```sh
curl -fsSL https://raw.githubusercontent.com/anpawo/Video-Code/main/scripts/install.sh | sh
```

It downloads the [latest release](https://github.com/anpawo/Video-Code/releases/latest)
for this machine — macOS on Apple Silicon, or Ubuntu 24.04 on x86_64 — into
`./video-code`, then renders one scene to prove it works. The only thing it asks
of the machine is `ffmpeg`: `brew install ffmpeg`, or on Ubuntu
`sudo apt install ffmpeg mesa-vulkan-drivers libvulkan1 libopengl0 libegl1 libglx0 libxkbcommon0`.

To build from source instead, checkout the [documentation](docs/user/user.md#installation).
