    #!/bin/bash


# README_HEADER=docs/readme/01_header.md
README_CODE=docs/readme/02_code.md
TUTORIAL_SCENE=docs/by-example/tuto.py
README_GIF=docs/readme/example.gif

# code file
printf '\n%s\n%s\n%s\n%s\n%s\n' \
  '<details>' \
  '<summary>Show tutorial code</summary>' \
  "$(printf '\n```py\n%s\n```\n' "$(cat "$TUTORIAL_SCENE")")" \
  '</details>' \
  '' > "$README_CODE"

# preview video source
./video-code --file "$TUTORIAL_SCENE" --generate output.mp4

# gif file
ffmpeg -i output.mp4 \
  -vf "fps=8,scale=560:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=48[p];[s1][p]paletteuse=dither=bayer:bayer_scale=2" \
  "$README_GIF" -y

# concatenate the files
(for file in docs/readme/*.md; do cat "$file"; echo; done) > README.md
