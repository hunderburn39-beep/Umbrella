#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REV=594ca2a494104df559a907db7c8f5602a93b2078
REPO=https://github.com/nukeykt/Nuked-MD.git
SRC="$ROOT/third_party/Nuked-MD"
OUT="$ROOT/build"
mkdir -p "$ROOT/third_party" "$OUT"
if [[ ! -d "$SRC/.git" ]]; then git clone "$REPO" "$SRC"; fi
[[ "$(git -C "$SRC" remote get-url origin)" == "$REPO" ]]
git -C "$SRC" fetch origin "$REV"
git -C "$SRC" archive "$REV" | tar -x -C "$OUT"
python3 "$ROOT/diagnostic.py" "$OUT"
python3 "$ROOT/port.py" "$OUT"
cp "$ROOT"/nx_frontend.{c,h} "$OUT/"
if [[ "${1:-build}" == prepare ]]; then exit 0; fi
: "${DEVKITPRO:=/opt/devkitpro}"
: "${DEVKITA64:=$DEVKITPRO/devkitA64}"
export DEVKITPRO DEVKITA64
export PATH="$DEVKITA64/bin:$DEVKITPRO/tools/bin:$DEVKITPRO/portlibs/switch/bin:$PATH"
SDL="$DEVKITPRO/portlibs/switch/bin/sdl2-config"
test -x "$SDL"
cd "$OUT"
sources=(68k.c arbiter.c cartridge.c controller.c fc1004.c fm.c iochip.c md.c tmss.c vdp.c z80.c vram.c audio.c video.c savestate.c nx_frontend.c)
aarch64-none-elf-gcc -std=gnu11 -O3 -g -march=armv8-a+crc+crypto -mtune=cortex-a57 -mtp=soft -fPIE -ffunction-sections -fdata-sections -D__SWITCH__ -I"$DEVKITPRO/libnx/include" -I"$DEVKITPRO/portlibs/switch/include" $("$SDL" --cflags) "${sources[@]}" -specs="$DEVKITPRO/libnx/switch.specs" -Wl,--gc-sections -L"$DEVKITPRO/libnx/lib" -L"$DEVKITPRO/portlibs/switch/lib" $("$SDL" --static-libs) -lm -lnx -o Umbrella-MegaDrive-NX.elf
nacptool --create "Umbrella Mega Drive NX" "Umbrella / Nuked-MD contributors" "1.0" Umbrella-MegaDrive-NX.nacp
elf2nro Umbrella-MegaDrive-NX.elf Umbrella-MegaDrive-NX.nro --nacp=Umbrella-MegaDrive-NX.nacp
mkdir -p "$ROOT/dist"
cp Umbrella-MegaDrive-NX.nro "$ROOT/dist/"
echo "NRO built; hardware test still required."
