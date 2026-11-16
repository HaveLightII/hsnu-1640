#!/bin/sh
set -eu

command -v cwebp >/dev/null 2>&1 || { echo "請先安裝 cwebp（libwebp）" >&2; exit 1; }
command -v dwebp >/dev/null 2>&1 || { echo "請先安裝 dwebp（libwebp）" >&2; exit 1; }
scriptDir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
resourceDir="$scriptDir/../src-tauri/gen/android/app/src/main/res"

for iconPath in "$resourceDir"/mipmap-*/ic_launcher*.png; do
    [ -f "$iconPath" ] || continue
    cwebp -quiet -q 85 -m 6 -metadata none "$iconPath" -o "${iconPath%.png}.webp"
    rm -- "$iconPath"
done

iconPath="$scriptDir/../src-tauri/icons/icon.png"
tempIcon=$(mktemp)
trap 'rm -f "$tempIcon"' EXIT HUP INT TERM
cwebp -quiet -lossless -resize 64 64 "$iconPath" -o "$tempIcon"
dwebp -quiet "$tempIcon" -o "$iconPath"
touch "$scriptDir/../src-tauri/tauri.conf.json"
