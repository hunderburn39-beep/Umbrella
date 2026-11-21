#!/usr/bin/env python3
"""Adapt the pinned upstream CPU scheduler to Emscripten's fiber API."""
import pathlib
import sys

def patch(s):
    pairs = [
        ('#elif defined(__APPLE__) || defined(RC_ASM_FIBERS)', '''#elif defined(__EMSCRIPTEN__)
#include <emscripten/fiber.h>
static emscripten_fiber_t sched_fiber, cpu_fiber[2];
static void *cpu_c_stack[2], *cpu_async_stack[2], *sched_async_stack;
static void fiber_switch_to_cpu(int w) { emscripten_fiber_swap(&sched_fiber, &cpu_fiber[w]); }
static void fiber_switch_to_sched(void) { emscripten_fiber_swap(&cpu_fiber[rc_cpu], &sched_fiber); }
#elif defined(__APPLE__) || defined(RC_ASM_FIBERS)'''),
        ('#elif defined(RC_CTX_FIBERS)\nstatic void fiber_proc(int w)', '''#elif defined(__EMSCRIPTEN__)
static void fiber_proc(void *p) { cpu_main((int)(intptr_t)p); }
#elif defined(RC_CTX_FIBERS)
static void fiber_proc(int w)'''),
        ('#elif defined(RC_CTX_FIBERS)\n    for (int w = 0; w < 2; w++) {', '''#elif defined(__EMSCRIPTEN__)
    if (!sched_async_stack) sched_async_stack = malloc(FIBER_STACK);
    if (!sched_async_stack) abort();
    emscripten_fiber_init_from_current_context(&sched_fiber, sched_async_stack, FIBER_STACK);
    for (int w = 0; w < 2; w++) {
        if (!cpu_c_stack[w]) cpu_c_stack[w] = malloc(FIBER_STACK);
        if (!cpu_async_stack[w]) cpu_async_stack[w] = malloc(FIBER_STACK);
        if (!cpu_c_stack[w] || !cpu_async_stack[w]) abort();
        emscripten_fiber_init(&cpu_fiber[w], fiber_proc, (void *)(intptr_t)w,
            cpu_c_stack[w], FIBER_STACK, cpu_async_stack[w], FIBER_STACK);
    }
#elif defined(RC_CTX_FIBERS)
    for (int w = 0; w < 2; w++) {'''),
    ]
    for old, new in pairs:
        if s.count(old) != 1:
            raise ValueError("Unexpected upstream runtime; refusing to patch: " + old)
        s = s.replace(old, new, 1)
    return s

if __name__ == "__main__":
    p = pathlib.Path(sys.argv[1])
    original = p.read_text()
    p.write_text(patch(original))
