#!/bin/bash


# README_HEADER=docs/readme/01_header.md
README_CODE=docs/readme/02_code.md
README_GIF=docs/readme/example.gif

# code file
printf '\n%s\n%s\n%s\n' '```py' "$(cat video.py)" '```' > "$README_CODE"

# video file (doesn't change)

# gif file
ffmpeg '-i' output.mp4 "$README_GIF" '-y'

# concatenate the files
(for file in docs/readme/*.md; do cat "$file"; echo; done) > README.md
