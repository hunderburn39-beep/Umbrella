#!/usr/bin/env bash
# Local build only. Generated game code is derived from the user's ROM.
# Do not commit or redistribute the resulting binary or original ROM.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
rom="$(realpath "${1:?Usage: build-local.sh /path/to/shangon.zip [output-directory]}")"
out="$(realpath -m "${2:-$here/local-build}")"
rev=4f5f25f1c680c53946323e0bf9a1cf8bfb4f72c2
python3 "$here/verify-pcb.py" "$rom"
for tool in git python3 emcc cc node; do command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }; done
test -f "$rom"
mkdir -p "$out"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
git clone https://github.com/chaotix359/Super-Hang-On-Ultimate.git "$work/upstream"
cd "$work/upstream"
git checkout --detach "$rev"
# setup.py generates and checks the translated game locally against the reference.
python3 setup.py --rom "$rom" --cc cc
cd source
python3 "$here/patch-wasm-fibers.py" src/rc_runtime.c
cat recomp/overrides/*.c > "$work/overrides_all.c"
M=src/third_party/musashi
emcc -O2 -DNDEBUG -fno-strict-aliasing -ffp-contract=off -w -Isrc \
  "$here/bridge.c" "$work/overrides_all.c" \
  src/rc_runtime.c src/gen/main_rc.c src/gen/sub_rc.c \
  src/sho_core.c src/sho_video.c src/sho_music.c src/sho_md.c \
  src/sho_mdgfx.c src/sho_mdcourse.c src/sho_mdsnd.c \
  "$M/m68kcpu.c" "$M/m68kops.c" "$M/m68kdasm.c" "$M/softfloat/softfloat.c" \
  src/third_party/z80/z80.c src/third_party/nukedopn2/ym3438.c \
  src/third_party/nukedopm/opm.c src/third_party/puff/puff.c \
  -sMODULARIZE=1 -sEXPORT_NAME=createShoModule -sALLOW_MEMORY_GROWTH=1 \
  -sFORCE_FILESYSTEM=1 -sEXPORTED_RUNTIME_METHODS=FS,ccall \
  -sASYNCIFY=1 -sASYNCIFY_STACK_SIZE=8388608 -sSTACK_SIZE=8388608 -sINITIAL_MEMORY=100663296 \
  -sENVIRONMENT=web,node --no-entry -o "$out/sho.js"
cp tests/selftest_1200.txt "$out/selftest_1200.txt"
cp "$here/player.html" "$out/index.html"
test -s "$out/sho.js"
test -s "$out/sho.wasm"
node "$here/verify-wasm.cjs" "$out" "$rom"
echo "Local files created in $out. Serve over HTTPS for motion permissions."
echo "Do not publish generated WASM containing SEGA-derived code."
