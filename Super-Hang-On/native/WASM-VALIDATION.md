# Original ROM WASM validation

Locally compiled with Emscripten 3.1.74 recovered from source-only SDK Actions run 44967954793, using the owner-supplied ROM and pinned source revision.

- 1200/1200 machine-state hashes match native upstream reference.
- Translated dispatches: 5984.
- Interpreted fallback instructions: 0 during the test.
- Sound commands: 9536; FM writes: 64694; PCM writes: 67604.
- Node test elapsed: 12.954 seconds (not a mobile benchmark).
- WASM SHA256: `1751788d5792b0432b64a79eaeebf238aabcb2bf173fdd14a686044d645cba62`.

Generated ROM-derived code is not committed or published. Standalone HTML prepared privately for the owner, requires their ZIP at runtime. Physical iPhone Safari and motion input not yet tested. This is reference-state equivalence for the specified sequence, not a claim of full physical PCB equivalence.
