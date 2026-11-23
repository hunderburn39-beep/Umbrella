# VDP handshake: captured evidence and next boot gate (2026-11-23)

## Source
User-supplied `vdp-handshake-trace.txt`: 96 rows, final master clock 1,396,093.
All sampled CPU writes target internal word address `0x600002`, corresponding
to the physical VDP control port `0xC00004` when converted to byte addresses.

## What the capture actually proves
- `cpu_as=0` and `cpu_rw=0` in all recorded rows: these are sampled writes.
- The VDP acknowledge signal (`vdp_ack`) falls 24 times in the sampled rows;
  board `dtack` also falls 24 times. This is evidence of handshaking, not
  a complete electrical timing verification.
- The register-1 command `0x8104` has bit 6 clear, so display enable is off.
- `reg_disp` stays zero in all captured rows. `reg_m5` becomes one.
- The last captured command is `0x9700` (VDP register 23). A later
  display-enable write is **not excluded** by this bounded capture.
- The initial `0x4741` sample is not a register write. Do not count it as one.
- Do not infer visible video or actual CPU instruction retirement from this trace.

## Why the old capture ended
The V5.5 sampler publishes an immutable snapshot at 96 *state changes*, not
after 96 completed CPU writes. Its first capture filled at master clock 1,396,093.
V5.6 extends this to 512 changes or 10,000,000 clocks, whichever occurs first.
It still does not prove that the CPU runs beyond that limit.

## Next gate
1. Build the current pinned source and run existing Python tests.
2. Capture a new `vdp-handshake-trace.txt` and `cpu-bus-trace.txt` on Switch.
3. Determine whether a later register-1 write sets bit 6 (`0x40`).
4. If no later write appears, correlate CPU bus activity and PC progression
   before changing the VDP logic.
5. If display enable appears but no pixels, inspect VRAM/CRAM initialization
   and scanline output, not just the SDL renderer.

## Constraints
Do not enable forced DTACK, synthesize a ROM instruction, or inject a fake
display-enable command as a 'fix'. Those would mask the fault.
The V5.6 source update is not a tested Switch binary.
