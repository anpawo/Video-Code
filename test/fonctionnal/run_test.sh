#!/bin/bash

SCRIPT_DIR="test/fonctionnal/scripts"

for FILE in "$SCRIPT_DIR"/*; do
  if [[ -f "$FILE" ]]; then
    echo -n "Processing $FILE... "
    ./video-code --sourceFile "$FILE" --generate test_out.mp4 > /dev/null 2>&1
    if [[ $? -eq 0 && -f "test_out.mp4" ]]; then
      rm "test_out.mp4"
      echo "Success"
    else
      echo "Failed"
    fi
  fi
done
