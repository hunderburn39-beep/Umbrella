#!/bin/sh
set -eu
cd "$(dirname "$0")"
src=vendor/blastem
mkdir -p vendor
if [ ! -d "$src/.git" ]; then
 git clone https://github.com/aarontodd82/blastem-genesis-engine.git "$src"
fi
git -C "$src" checkout --detach 20cf4b5beae0a848fb17b9c36dc955167acc1ae5
cd "$src"
make CPU=arm64 NEW_CORE=1 m68k.c z80.c
printf '%s\n' 'Generated CPU sources; libnx bus adapter and linking still required.'
