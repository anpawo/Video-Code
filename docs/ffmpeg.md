# Documentation about ffmpeg

## Arguments

- `-i`
input file (can have many)

- `-filter_complex`
complex filter to apply on many inputs/outputs (filter;filter;...)
  - `concat` concatenate 2 video, one after the other
  - `overlay` place one video on top of another video at a certain position. W/H = main video width/height, w/h = overlay video width/height
  - `hstack` stack 2 video horizontally


- `-vf`
video filter to apply on one video stream
  - `scale` scale the video
  - `format` change the format (grayscale for example)

- `-af`
audio filter to apply on one audio stream
  - `volume` change the volume

- `-map`
maps a stream to the output file. e.g. the concat filters will have some output stream that you can redirect (map) into the output file.

## Vocabulary
- `stream`
part of a video/image
  - `video`
  - `audio`
  - `subtitle`
  - `metadata`
