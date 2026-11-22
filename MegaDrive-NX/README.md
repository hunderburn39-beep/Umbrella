# Umbrella Mega Drive NX V0.3
Experimental Nintendo Switch homebrew port of Nuked-MD. No FPGA board required. It is a software simulation of the reconstructed chip logic rather than physical FPGA execution. Full speed is not established; upstream explicitly notes its simulation is very slow. Includes an original CC0 diagnostic ROM. Without a user ROM, it boots the diagnostic automatically. The screen backdrop should change with controller directions/B/C. This is a diagnostic, not a full game.

## Build
Use devkitPro with switch-dev, switch-sdl2, Git, Bash and Python 3.
    bash build.sh prepare
    bash build.sh
The first command generates patched source; the second additionally attempts cross-compilation and NRO packaging. Expected output: dist/Umbrella-MegaDrive-NX.nro. No compiled binary is present yet.

## Install after a successful build
Copy the NRO to /switch/Umbrella-MegaDrive-NX/Umbrella-MegaDrive-NX.nro on the SD card of an already homebrew-enabled Nintendo Switch. Place raw legally obtained ROMs (.bin, .md, .gen) in /switch/Umbrella-MegaDrive-NX/roms/. Launch via Homebrew Menu in application mode. A legitimately obtained optional tmss.bin can be placed next to the NRO; upstream supports a dummy TMSS fallback. Initial version supports one three-button controller, raw ROMs only, NTSC default.

## Controls
Directional pad/left stick: movement. Y/B/A: Mega Drive A/B/C. Plus: Start. Minus: exit. The ROM list uses A to select and B to exit.

## Validation
Pending: actual compilation/link, launch, frame timing, audio, PAL, mapper, controller and hardware tests. Audio bridge uses SDL resampling; does not guarantee uninterrupted sound. The upstream software simulation is computationally expensive and may be far slower than original hardware. This port is not a playable release.

## License
Nuked-MD by nukeykt and contributors: GPL-2.0-or-later where specified by upstream. Source revision: 594ca2a494104df559a907db7c8f5602a93b2078. https://github.com/nukeykt/Nuked-MD
Preserve all upstream notices and licenses. Redistribute corresponding source and build scripts with any binaries under applicable GPL terms. Frontend adaptations GPL-2.0-or-later.
