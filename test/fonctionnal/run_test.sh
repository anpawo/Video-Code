#!/bin/bash

GREEN="\e[32m"
RED="\e[31m"

SCRIPT_DIR="test/fonctionnal/scripts"

for FILE in "$SCRIPT_DIR"/*; do
  if [[ -f "$FILE" ]]; then
    printf "%-50s" "$FILE"
    ./video-code --sourceFile "$FILE" --generate test_out.mp4 > /dev/null 2>&1
    if [[ $? -eq 0 && -f "test_out.mp4" ]]; then
      rm "test_out.mp4"
      printf "${GREEN} [OK] ${NC}\n"
    else
      printf "${RED} [KO] ${NC}\n"
    fi
  fi
done
