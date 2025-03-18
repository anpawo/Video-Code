#!/bin/bash

GREEN="\e[32m"
RED="\e[31m"
NC="\033[0m"

SCRIPT_DIR="test/fonctionnal/scripts"

success=0
failure=0

if [[ ! -d "$SCRIPT_DIR" ]]; then
  echo "Error: Directory $SCRIPT_DIR does not exist."
  exit 1
fi
if [[ ! -f "video-code" ]]; then
  echo "Error: video-code executable not found."
  exit 1
fi
if [[ ! -x "video-code" ]]; then
  echo "Error: video-code is not executable."
  exit 1
fi

printf "======================running tests======================\n"
printf "=========================================================\n"
for FILE in "$SCRIPT_DIR"/*; do
  if [[ -f "$FILE" ]]; then
    printf "%-52s" "$FILE"
    ./video-code --sourceFile "$FILE" --generate test_out.mp4 > /dev/null 2>cache
    if [[ $? -eq 0 && -f "test_out.mp4" ]]; then
      success=$((success + 1))
      rm "test_out.mp4"
      printf "${GREEN} [OK] ${NC}\n"
    else
      failure=$((failure + 1))
      printf "${RED} [KO] ${NC}\n"
      echo "Error: $(cat cache)"
      rm cache
    fi
  fi
done

rm cache
printf "=========================================================\n"
printf "Total: ${GREEN}$(($success + $failure))${NC}\n"
printf "Success: ${GREEN}$success${NC}\n"
printf "Failure: ${RED}$failure${NC}\n"
printf "=========================================================\n"
printf "success rate: ${GREEN}$(($success * 100 / ($success + $failure)))%%${NC}\n"
printf "=========================================================\n"
printf "All tests completed.\n"
