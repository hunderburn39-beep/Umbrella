/* Synthetic ROM-free test of the linked board. Never used in the playable build. */
#include <stdint.h>
#include <stdlib.h>
#include <emscripten/emscripten.h>
#include "sho_core.h"
#include "sho_internal.h"
#include "rc_runtime.h"

static unsigned ticks[2], frames;
static void diagnostic_loop(uint32_t entry) {
    (void)entry;
    for (;;) {
        ++ticks[rc_cpu];
        REG_PC = 0x1000;
        USE_CYCLES(10);
        STEP();
    }
}
const rc_fn M_table[0x20000] = { [0x800] = diagnostic_loop };
const rc_fn S_table[0x20000] = { [0x800] = diagnostic_loop };

EMSCRIPTEN_KEEPALIVE int diagnostic_boot(void) {
    if (M) return 0;
    M = calloc(1, sizeof *M);
    if (!M) return 0;
    uint8_t *roms[2] = { M->mrom, M->srom };
    for (int i=0; i<2; ++i) {
        be16w(roms[i], 0, 0x0006);
        be16w(roms[i], 2, 0x2000);
        be16w(roms[i], 4, 0);
        be16w(roms[i], 6, 0x1000);
        be16w(roms[i], 0x1000, 0x60fe); /* synthetic BRA -2 */
    }
    extern int sho_recomp;
    sho_recomp = 1;
    sho_reset();
    sho_set_view_width(320);
    return 1;
}
EMSCRIPTEN_KEEPALIVE void diagnostic_step(void) {
    int16_t audio[1600];
    sho_input input = {0};
    sho_set_input(&input);
    sho_run_frame();
    sho_audio(audio, 800);
    ++frames;
}
EMSCRIPTEN_KEEPALIVE unsigned diagnostic_frames(void) {return frames;}
EMSCRIPTEN_KEEPALIVE unsigned diagnostic_ticks(unsigned cpu) {return cpu < 2 ? ticks[cpu] : 0;}
EMSCRIPTEN_KEEPALIVE unsigned diagnostic_width(void) {return sho_width();}
EMSCRIPTEN_KEEPALIVE unsigned diagnostic_height(void) {return SHO_H;}
EMSCRIPTEN_KEEPALIVE unsigned diagnostic_pixels(void) {return sho_framebuffer() != NULL;}
