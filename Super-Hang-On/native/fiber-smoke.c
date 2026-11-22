/* ROM-free test for WebAssembly cooperative CPU switching.
 * Runs the same Emscripten fiber API used by the actual 68000 adapter. */
#include <stdint.h>
#include <stdlib.h>
#include <emscripten/emscripten.h>
#include <emscripten/fiber.h>

enum { STACK = 128 * 1024 };
static emscripten_fiber_t scheduler, cpu[2];
static _Alignas(16) uint8_t cstack[2][STACK], astack[2][STACK], scheduler_stack[STACK];
static uint32_t counter[2], checksum[2];
static int initialized;
static void processor(void *arg) {
    unsigned id = (unsigned)(uintptr_t)arg;
    uint32_t local = 0x12345678u + id;
    for (;;) {
        local = local * 1664525u + 1013904223u;
        checksum[id] = local;
        ++counter[id];
        emscripten_fiber_swap(&cpu[id], &scheduler);
    }
}
EMSCRIPTEN_KEEPALIVE int init_test(void) {
    if (initialized) return 0;
    emscripten_fiber_init_from_current_context(&scheduler, scheduler_stack, STACK);
    for (unsigned i=0; i<2; ++i)
        emscripten_fiber_init(&cpu[i], processor, (void *)(uintptr_t)i,
            cstack[i], STACK, astack[i], STACK);
    initialized=1;
    return 1;
}
EMSCRIPTEN_KEEPALIVE int step_test(int lines) {
    if (!initialized || lines < 1 || lines > 262) return 0;
    for (int line=0; line<lines; ++line)
        for (unsigned i=0; i<2; ++i)
            emscripten_fiber_swap(&scheduler, &cpu[i]);
    return 1;
}
EMSCRIPTEN_KEEPALIVE uint32_t count_test(unsigned i) { return i<2 ? counter[i] : 0; }
EMSCRIPTEN_KEEPALIVE uint32_t hash_test(unsigned i) { return i<2 ? checksum[i] : 0; }
