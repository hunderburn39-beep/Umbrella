/* Browser bridge for the upstream Super Hang-On Ultimate portable core.
 * Native adapter only; not a standalone game. Requires upstream source and
 * user-supplied ROM data. No original ROM or generated game code included.
 * Upstream: https://github.com/chaotix359/Super-Hang-On-Ultimate (MIT project source).
 */
#include "sho_core.h"
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#define API EMSCRIPTEN_KEEPALIVE
#else
#define API
#endif
extern int sho_recomp;
static char error_text[256];
static sho_input input;
static int16_t audio_buffer[2 * 802];
static int audio_frames;
static double audio_phase;
static int loaded;
static uint32_t completed_frames;
static float bounded(float x, float low, float high) {
    if (!(x >= low)) return low;
    return x > high ? high : x;
}
API int browser_load(const char *rom_path) {
    loaded = 0;
    if (!rom_path) return -1;
    error_text[0] = 0;
    int result = sho_load_roms(rom_path, error_text, sizeof error_text);
    if (result) return result;
    sho_recomp = 1;
    sho_reset();
    /* Upstream arcade test runner uses these DIP settings for genuine Free Play. */
    sho_set_dips(0x00, 0xfe);
    sho_set_view_width(SHO_W);
    memset(&input, 0, sizeof input);
    completed_frames = 0;
    audio_phase = 0;
    audio_frames = 0;
    loaded = 1;
    return 0;
}
API const char *browser_error(void) { return error_text; }
API void browser_input(float steer, float throttle, float brake,
                       int turbo, int start, int coin,
                       int up, int down, int left, int right) {
    input.steer = bounded(steer, -1.f, 1.f);
    input.throttle = bounded(throttle, 0.f, 1.f);
    input.brake = bounded(brake, 0.f, 1.f);
    input.turbo = !!turbo;
    input.start = !!start;
    input.coin = !!coin;
    input.nav_up = !!up; input.nav_down = !!down;
    input.nav_left = !!left; input.nav_right = !!right;
}
API void browser_frame(void) {
    if (!loaded) return;
    sho_set_input(&input);
    sho_run_frame();
    audio_phase += 48000.0 / SHO_FPS;
    audio_frames = (int)audio_phase;
    audio_phase -= audio_frames;
    sho_audio(audio_buffer, audio_frames);
    completed_frames++;
}
API uint32_t browser_completed_frames(void) { return completed_frames; }
/* Same observation hash used by upstream's 1200-frame native test. */
extern uint64_t sho_state_hash(void);
extern unsigned long rc_stats_interp, rc_stats_dispatch;
extern unsigned long sho_debug_latch_writes, sho_debug_opm_writes, sho_debug_pcm_writes;
API uint32_t browser_hash_lo(void) { return loaded ? (uint32_t)sho_state_hash() : 0; }
API uint32_t browser_hash_hi(void) { return loaded ? (uint32_t)(sho_state_hash() >> 32) : 0; }
API uint32_t browser_translated_dispatches(void) { return (uint32_t)rc_stats_dispatch; }
API uint32_t browser_interpreted_instructions(void) { return (uint32_t)rc_stats_interp; }
API uint32_t browser_sound_commands(void) { return (uint32_t)sho_debug_latch_writes; }
API uint32_t browser_fm_writes(void) { return (uint32_t)sho_debug_opm_writes; }
API uint32_t browser_pcm_writes(void) { return (uint32_t)sho_debug_pcm_writes; }

API const uint32_t *browser_pixels(void) { return loaded ? sho_framebuffer() : NULL; }
API int browser_width(void) { return loaded ? sho_width() : 0; }
API int browser_height(void) { return SHO_H; }
API int browser_is_recompiled(void) { return loaded && sho_recomp == 1; }
API const int16_t *browser_audio(void) { return audio_buffer; }
API int browser_audio_frames(void) { return audio_frames; }
API void browser_view_width(int width) {
    if (loaded) sho_set_view_width(width < SHO_W ? SHO_W : width > SHO_MAX_W ? SHO_MAX_W : width);
}
API void browser_dips(uint8_t coinage, uint8_t switches) {
    if (loaded) sho_set_dips(coinage, switches);
}
