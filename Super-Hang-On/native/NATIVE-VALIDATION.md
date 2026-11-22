# Native ROM validation

Actual local execution on Linux x86_64, GCC 14.2.0 (Debian 14.2.0-19), using the supplied shangon(1).zip and source kit from Actions run 44967089412, revision 8446037b4eec853027bb665c09e1d175354a8eab.

- ROM integrity: 25 chips verified; 14 interrupt vectors checked.
- MAIN translation: 292 functions, 6347 instructions, 5 overrides applied.
- SUB translation: 43 functions, 1059 instructions.
- Native reference test: PASS, 1200/1200 machine-state hashes identical to the pinned upstream reference.
- SHA256 of both hash logs: `a467380aec2fc0ebbeaf78fcff35cf3d2f64d5afd4002c738fc476285232024e`.
- First state: `0 a8ede247c0239161`; last: `1199 68999fe67407c04c`.
- Exact test output: `SUCCESS: the generated code behaves exactly like the reference build (1200 frames identical).`

This validates the native test sequence, not pixel/audio equivalence against physical hardware or browser performance. The WASM build of the translated ROM and Safari gameplay remain pending. ROM bytes and generated binaries are not committed.
