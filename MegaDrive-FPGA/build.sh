#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REMOTE=https://github.com/MiSTer-devel/MegaDrive_MiSTer.git
REV=8f2716f48818c84e9677cd2526cee39fa958920e
SRC="$ROOT/third_party/MegaDrive_MiSTer"
MODE="${1:-prepare}"
case "$MODE" in prepare|build) ;; *) echo "Usage: bash build.sh [prepare|build]" >&2; exit 2;; esac
mkdir -p "$ROOT/third_party"
if [[ ! -d "$SRC/.git" ]]; then
  git clone --no-checkout "$REMOTE" "$SRC"
fi
[[ "$(git -C "$SRC" remote get-url origin)" == "$REMOTE" ]] || { echo "Unexpected upstream"; exit 1; }
if [[ -n "$(git -C "$SRC" status --porcelain --untracked-files=no)" ]] && git -C "$SRC" rev-parse --verify HEAD >/dev/null 2>&1; then
  # A fresh --no-checkout clone has no populated worktree; only accept it when HEAD is not checked out yet.
  if [[ -f "$SRC/MegaDrive.qpf" ]]; then echo "Upstream has local changes; aborting"; exit 1; fi
fi
git -C "$SRC" fetch origin "$REV"
git -C "$SRC" checkout --detach "$REV"
git -C "$SRC" submodule update --init --recursive
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$REV" ]]
for f in MegaDrive.qpf MegaDrive.qsf files.qip rtl/nuked-md.qip rtl/nuked-md/68k.v rtl/nuked-md/z80.v rtl/nuked-md/ym7101.v rtl/nuked-md/ym3438.v rtl/nuked-md/ym6045.v rtl/nuked-md/ym6046.v rtl/nuked-md/fc1004.v rtl/nuked-md/md_board.v rtl/nuked-md/vram.v; do
  test -s "$SRC/$f" || { echo "Missing $f" >&2; exit 1; }
done
echo "Pinned RTL present: $REV"
[[ "$MODE" == build ]] || exit 0
command -v quartus_sh >/dev/null || { echo "Quartus Prime with Cyclone V support is required" >&2; exit 1; }
cd "$SRC"
quartus_sh --flow compile MegaDrive
test -s output_files/MegaDrive.rbf
mkdir -p "$ROOT/dist"
cp output_files/MegaDrive.rbf "$ROOT/dist/Umbrella_MegaDrive_FPGA.rbf"
echo "RBF generated. Review fitter and TimeQuest reports before hardware use."
