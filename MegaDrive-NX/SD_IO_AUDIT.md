# Critical-path SD I/O audit (2026-11-23)

## Confirmed source conflict

- `port.py` patches the startup path to call `nx_disable_runtime_io()` before creating the simulation worker.
- `nx_frontend.c` uses that flag to suppress `nx_stage` writes, but it does **not** globally intercept `fopen`.
- `port.py` still inserts `fopen("sdmc:/switch/Umbrella-MegaDrive-NX/rom-boot-trace.txt", "w")` and `fopen("sdmc:/switch/Umbrella-MegaDrive-NX/cpu-bus-trace.txt", "w")` in `work_thread`.
- Therefore, the comment "runtime SD I/O disabled" is inaccurate for these two trace paths. A filesystem call in the chip simulation loop can stall the worker. This is a code-level risk, not proof of the current screen freeze.

## Required correction before relying on timing benchmarks

1. Worker captures bounded trace entries in preallocated memory only.
2. Publish a complete immutable snapshot with a release/acquire handoff.
3. Main thread writes the snapshot to SD at a safe point, without blocking the worker or racing on its buffer.
4. Report write failures and provide an on-screen fallback when SD access is unavailable.
5. Ensure that no `fopen`, `fprintf`, or `fclose` remains on the worker's hot path.
6. Confirm compilation and then benchmark on Switch hardware.

## Important diagnostic limitations

The current CPU trace is sampled at active address-strobe cycles. It is neither an instruction-PC trace nor a complete transaction log; repeated reads at the same address with unchanged flags may be suppressed. CPU output data during a read is not the data received by the CPU. Zero captured entries do not by themselves identify which chip is at fault.
