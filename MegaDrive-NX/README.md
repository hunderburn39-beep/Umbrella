# Umbrella Mega Drive NX V1.5
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

## Startup crash diagnosis (V0.4)
On the ROM menu, X boots the built-in diagnostic. After a crash, launch the app again and read 'Last stage' below the menu. The same marker is written to `/switch/Umbrella-MegaDrive-NX/last-stage.txt` on the SD card. Send the marker for targeted repair. Full-speed operation remains unverified.

## V0.5 TMSS/cartridge diagnostics
ROM start writes last-stage checkpoints 02a (TMSS complete), 03a-03g (cartridge file opening, file size, buffer clearing, read and byte swapping), and then continues to chip startup. After a crash reopen the app and photograph Last stage, or retrieve `/switch/Umbrella-MegaDrive-NX/last-stage.txt` via FTP. X runs built-in diagnostic. Experimental and unverified on Switch hardware.

## V0.6 TMSS isolation test
This diagnostic build forces the upstream built-in dummy TMSS rather than opening optional `tmss.bin`. It suppresses fallback stdout after closing the ROM selector console. Reopen after any error and send the `Last stage` line. A working system should progress beyond `02 Built-in TMSS start` to `02a TMSS ready` and then cartridge checkpoints. Hardware operation remains unverified.

## V0.7 Silent startup isolation
The console reached stage `07 Video ready` in V0.6. This diagnostic version bypasses **host audio device startup** while keeping the emulated FM/PSG chip logic. New checkpoints `07a Host audio bypassed` and `07b Controls initializing` narrow down a crash before stage `08 Controls ready`. The diagnostic still runs through the full chip simulation and may be extremely slow. Reopen after a crash to read `Last stage` or retrieve `last-stage.txt` by FTP. Audio output is intentionally silent for this version.

## V0.8: separate GPU startup from chip-thread crash
Before starting the Nuked-MD chip worker, the program now performs a single `Video_Blit()` with the prepared blank video buffers. If the Switch crashes there, Last stage remains `09 Single-thread video test`. Otherwise `09a Video test passed` confirms the SDL renderer can present with no emulation thread active. Subsequent markers `09 Creating worker thread`, `10 Worker created`, `11 Video loop started` and `11a Video blit returned` narrow down the next failure. This is a diagnostic build, not verified gameplay; audio output remains disabled.

## V0.9: chip-worker crash isolation
The video renderer completed a first SDL blit on actual Switch hardware (stage `11a`). This release writes a **separate** `worker-stage.txt`, displayed on the ROM menu as `Worker stage` after an exception. W00: not started; W01: thread entered; W02: loop entered; W03: 68000 clock; W04: Z80 clock; W05: FC1004 ASIC; W06: VRAM; W07: bus cycle; W08: audio/video update; W09: first complete clock; W10: 1000 clocks; W11: 100K; W12: 1M. Both `last-stage.txt` and `worker-stage.txt` are stored under `/switch/Umbrella-MegaDrive-NX/`. Instrumentation runs only on the first clock and at coarse milestones. Host audio remains muted pending validation. No claim of full-speed operation or functional gameplay.

## V1.0: periodic chip-phase crash checkpoints
After stage `11a` video presentation and `W11` at 100K clocks were observed on the Switch, this diagnostic build adds `Worker stage: C<number> <phase>` snapshots every 32768 master-clock cycles. Phases are 68000, Z80, FC1004, VRAM, BUS, AUDIO VDP. The on-screen marker names the last *checkpoint reached*; it may not be the exact instruction that failed. An exception may still be caused by a graphics, synchronization, or operating-system failure. Device audio remains disabled. After a crash reopen the app and photograph both stage lines. A screenshot of a cycle marker is not proof that gameplay has started.

## V1.1: isolate the audio sample mixer
The actual Switch log is `Last stage 11a Video blit returned`, `Worker stage C196608 AUDIO VDP`, which records **196608** master clocks, not millions. Previous V1.0 output does not prove which instruction crashed. V1.1 leaves the YM2612, PSG and other chips clocked inside Nuked-MD, but bypasses `Audio_Update()` (the host sample aggregation routine) in the worker loop, while host sound output remains muted. The stage labels are updated to `VDP` and `W08 Video update OK`. If an exception occurs, reopen and report the last stage and worker stage. The output still needs hardware validation and does not claim playable game speed.

## V1.2 raster isolation (Y selector)
The Switch crash persisted around `Worker stage C163840 VDP` after bypassing host audio mixing in V1.1; that marker does not establish the exact cause. Select a ROM with **A** for the normal simulation or **Y** for a diagnostic run that bypasses `Video_PlotVDP()` only, while continuing 68000, Z80, FC1004, VDP clock logic and SDL screen presentation. The Y-mode screen will remain black by design and is not a gameplay mode. It adds `NR` to the `Worker stage` cyclic markers. Reopen the app after a fault to compare cycle counts for normal vs Y mode. X continues to load the built-in diagnostic with normal raster. Host audio remains intentionally muted. This is not confirmed playable on Switch.


## V1.3 performance isolation
On Switch V1.2, Y mode (raster off) reached C393216 VDP NR compared with C163840 in V1.1, without proving that raster is the cause. V1.3 avoids redundant screen texture uploads and presents until the VDP has completed another frame, reduces the host SDL loop from approximately 1000 iterations/sec to 60, and limits SD diagnostic writes to **one per 32768 simulated master clocks** instead of six. 'Worker stage' now includes 'T<number>s' as elapsed time since the first progress marker. The same A normal and Y no-raster comparison remains. The underlying chip emulation logic is unchanged; host sound output and audio sample mixing remain disabled for diagnosis. Chip clock speed, gameplay, and stability are not yet established.

## V1.4: SDL title-call isolation and controlled-shutdown marker
V1.3 on the Switch displayed `Worker stage C327680 CLOCK T6s` and `Last stage 11a Video blit returned`. This indicates approximately 55K simulated master-clock cycles/s over the observed interval and extremely poor real-time performance compared with the ~1.79M clocks required per frame. V1.4 removes the repeated `Video_UpdateTitle`/`SDL_SetWindowTitle` call from the 16ms main loop, which does not display a usable title on the Switch and could be contributing to platform instability. The two ROM-selector modes, chip logic, video throttling and stage sampling remain as before. If the user exits deliberately through the app, `Last stage 12 Controlled shutdown` is recorded; if the Switch closes the application unexpectedly, the previous stage remains. Performance is not guaranteed, and this version is a diagnostic, not verified playable.

## V1.5: filesystem IPC crash fix candidate
An Atmosphere v1.7 report for the **exact V1.4 NRO** (rebuild SHA256 matched release) identified Data Abort NULL access near `_fsFsOpenCommon` in libnx, associated with filesystem open/session handling, rather than an instruction in the 68000/Z80 simulation. V1.4 `nx_worker_stage()` opened `/switch/Umbrella-MegaDrive-NX/worker-stage.txt` from the chip worker on every 32768-clock progress event. V1.5 removes **all fopen/fclose/formatting** from chip worker stage functions; they publish an atomic in-memory snapshot. `nx_flush_worker_stage()` on the main SDL thread alone persists this to SD, no more often than every 1.2 seconds, and only when the content changes; W00 is written on launch. That should eliminate the observed high-frequency worker-thread FS IPC path. This is a hypothesis supported by symbolication, pending real console confirmation. A normal launch is A; Y remains raster bypass; host audio and sample mixing still disabled for isolation. Stage persistence is intentionally asynchronous: last stage may lag up to ~1.2s. Performance and full gameplay not validated.
