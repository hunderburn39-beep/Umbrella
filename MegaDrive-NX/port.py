#!/usr/bin/env python3
"""Adapt pinned Nuked-MD for libnx. Original GPL notices are retained."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def load(f): return (root/f).read_text()
def save(f,s): (root/f).write_text(s)
def replace(s,a,b):
    if s.count(a)!=1: raise RuntimeError("Upstream mismatch: "+a[:90])
    return s.replace(a,b,1)
s=load("md.c")
s=replace(s,'#include "SDL.h"','#include "SDL.h"\n#include <switch.h>\n#include "nx_frontend.h"')
s=replace(s,'    char *rom_filename = "rom.bin";','    char *rom_filename = "sdmc:/switch/Umbrella-MegaDrive-NX/rom.bin";')
s=replace(s,'    char *tmss_filename = "tmss.bin";','    char *tmss_filename = "sdmc:/switch/Umbrella-MegaDrive-NX/tmss.bin";')
s=replace(s,'    if (*argv)\n        rom_filename = *argv;', '''    if (*argv)
        rom_filename = *argv;
    if (!nx_choose_rom(&rom_filename)) return 0;''')
s=replace(s,'        printf("%s not found\\n", rom_filename);\n        exit(EXIT_FAILURE);','        nx_error("ROM invalid or unreadable");\n        return EXIT_FAILURE;')
s=replace(s,'    Audio_Init(audioout_filename, md.ntsc);\n    Video_Init(videoout_filename, md.ntsc);','''    SDL_SetMainReady();
    if (SDL_Init(0) != 0) { nx_error(SDL_GetError()); return EXIT_FAILURE; }
    if (!nx_video_init(md.ntsc)) { SDL_Quit(); nx_error("Video initialization failed"); return EXIT_FAILURE; }
    Audio_Init(audioout_filename, md.ntsc);
    nx_pad_init();''')
s=replace(s,'    if (!thread)\n    {\n        Audio_Shutdown();','    if (!thread)\n    {\n        nx_error("Worker thread creation failed");\n        Audio_Shutdown();')
s=replace(s,'        SDL_Delay(30);','        SDL_Delay(1);\n        if (!appletMainLoop() || nx_pad_poll()) quit_signal = 1;')
s=replace(s,'            printf("frame %lld\\n", (long long)(mcycles / frame_div));','            (void)frame_div;')

# Persist startup checkpoints to diagnose native Switch exceptions.
s=replace(s,'    if (!nx_choose_rom(&rom_filename)) return 0;',
  '    if (!nx_choose_rom(&rom_filename)) return 0;\n    nx_stage("01 ROM selected");')
# On Switch, isolate failure by using the upstream embedded TMSS fallback.
s=replace(s,'    if (load_tmss_rom(tmss_filename))',
  '    nx_stage("02 Built-in TMSS start");\n    if (1)')
s=replace(s,'    init_chips();',
  '    nx_stage("03 Cartridge loaded");\n    init_chips();')
s=replace(s,'    FC1004_Init(&ym);',
  '    FC1004_Init(&ym);\n    nx_stage("04 Chip init complete");')
s=replace(s,'    SDL_SetMainReady();',
  '    nx_stage("05 SDL starting");\n    SDL_SetMainReady();')
s=replace(s,'    if (!nx_video_init(md.ntsc))',
  '    nx_stage("06 SDL base ready");\n    if (!nx_video_init(md.ntsc))')
s=replace(s,'    Audio_Init(audioout_filename, md.ntsc);',
  '    nx_stage("07 Video ready");\n    Audio_Init(audioout_filename, md.ntsc);')
s=replace(s,'    nx_pad_init();',
  '    nx_pad_init();\n    nx_stage("08 Audio and controls ready");')
s=replace(s,'    thread = SDL_CreateThread(work_thread, "work thread", 0);',
  '    nx_stage("09 Creating worker thread");\n    thread = SDL_CreateThread(work_thread, "work thread", 0);')
s=replace(s,'    int quit_signal = 0;',
  '    nx_stage("10 Worker created");\n    int quit_signal = 0;')
s=replace(s,'        Video_Blit();',
  '        if (first_blit) { nx_stage("11 Video loop started"); first_blit = 0; }\n        Video_Blit();')
s=replace(s,'    int quit_signal = 0;',
  '    int first_blit = 1;\n    int quit_signal = 0;')

# Remove stdout use from the TMSS fallback; its selector console is closed.
s=replace(s,'        printf("%s not found\\n", tmss_filename);',
  '        /* Using built-in TMSS diagnostic fallback. */')

# Mute host audio output to isolate the crash after video initialized.
# The FM and PSG chip logic still runs in the motherboard simulation.
s=replace(s,'    nx_stage("07 Video ready");\n    Audio_Init(audioout_filename, md.ntsc);',
  '    nx_stage("07 Video ready");\n    nx_stage("07a Host audio bypassed");')
s=replace(s,'    nx_pad_init();\n    nx_stage("08 Audio and controls ready");',
  '    nx_stage("07b Controls initializing");\n    nx_pad_init();\n    nx_stage("08 Controls ready");')

# Distinguish TMSS completion from cartridge loading.
s=replace(s,'        load_dummy_tmss();\n    }\n    if (cart_load_game_rom',
  '        load_dummy_tmss();\n    }\n    nx_stage("02a TMSS ready");\n    if (cart_load_game_rom')

# V0.8: render a frame *before* the chip worker is created. The previous
# V0.7 stage 11 could represent either SDL rendering or a worker crash.
s=replace(s,'    work_thread_run = 1;\n    nx_stage("09 Creating worker thread");',
  '    nx_stage("09 Single-thread video test");\n    Video_Blit();\n    nx_stage("09a Video test passed");\n    work_thread_run = 1;\n    nx_stage("09 Creating worker thread");')
s=replace(s,'    int first_blit = 1;',
  '    int first_blit = 1;\n    int first_post_blit = 1;')
s=replace(s,'        Video_Blit();\n    }\n    while (!quit_signal);',
  '        Video_Blit();\n        if (first_post_blit) { nx_stage("11a Video blit returned"); first_post_blit = 0; }\n    }\n    while (!quit_signal);')

# V0.9: separate the chip worker from main video progress.
s=replace(s,"int SDLCALL work_thread(void *data)\n{\n    int i;","int SDLCALL work_thread(void *data)\n{\n    int i;\n    nx_worker_stage(\"W01 Worker thread entered\");")
s=replace(s,"    while (work_thread_run)\n    {\n        const int frame_div = 1789772;","    while (work_thread_run)\n    {\n        if (mcycles == 0) nx_worker_stage(\"W02 Chip loop entered\");\n        const int frame_div = 1789772;")
s=replace(s,"            // z80\n            z80.input.ext_data_i = md.zdata;","            if (mcycles == 0 && i == 0) nx_worker_stage(\"W03 M68K clock OK\");\n            // z80\n            z80.input.ext_data_i = md.zdata;")
s=replace(s,"            // fc1004\n            ym.vdp.input.i_csync","            if (mcycles == 0 && i == 0) nx_worker_stage(\"W04 Z80 clock OK\");\n            // fc1004\n            ym.vdp.input.i_csync")
s=replace(s,"            // VRAM\n            update_vram();","            if (mcycles == 0 && i == 0) nx_worker_stage(\"W05 FC1004 clock OK\");\n            // VRAM\n            update_vram();\n            if (mcycles == 0 && i == 0) nx_worker_stage(\"W06 VRAM update OK\");")
s=replace(s,"        Audio_Update();","        if (mcycles == 0) nx_worker_stage(\"W07 Chip bus cycle OK\");\n        Audio_Update();")
s=replace(s,"        md.odclk = ym.vdp.input.i_clk1;","        if (mcycles == 0) nx_worker_stage(\"W08 Audio/video update OK\");\n        md.odclk = ym.vdp.input.i_clk1;")
s=replace(s,"        mcycles++;\n    }\n    return 0;","        mcycles++;\n        if (mcycles == 1) nx_worker_stage(\"W09 First full clock OK\");\n        else if (mcycles == 1000) nx_worker_stage(\"W10 1000 clocks OK\");\n        else if (mcycles == 100000) nx_worker_stage(\"W11 100K clocks OK\");\n        else if (mcycles == 1000000) nx_worker_stage(\"W12 1M clocks OK\");\n    }\n    return 0;")
s=replace(s,"    nx_stage(\"09 Creating worker thread\");","    nx_worker_stage(\"W00 Worker not started\");\n    nx_stage(\"09 Creating worker thread\");")

# V1.0: periodic phase snapshots (every 32768 master-clock cycles)
s=replace(s,"            // z80\n            z80.input.ext_data_i = md.zdata;","            if (mcycles && ((mcycles & 32767) == 0) && i == 0) nx_worker_progress((unsigned long long)mcycles,\"68000\");\n            // z80\n            z80.input.ext_data_i = md.zdata;")
s=replace(s,"            // fc1004\n            ym.vdp.input.i_csync","            if (mcycles && ((mcycles & 32767) == 0) && i == 0) nx_worker_progress((unsigned long long)mcycles,\"Z80\");\n            // fc1004\n            ym.vdp.input.i_csync")
s=replace(s,"            // VRAM\n            update_vram();","            if (mcycles && ((mcycles & 32767) == 0) && i == 0) nx_worker_progress((unsigned long long)mcycles,\"FC1004\");\n            // VRAM\n            update_vram();\n            if (mcycles && ((mcycles & 32767) == 0) && i == 0) nx_worker_progress((unsigned long long)mcycles,\"VRAM\");")
s=replace(s,"        Audio_Update();","        if (mcycles && ((mcycles & 32767) == 0)) nx_worker_progress((unsigned long long)mcycles,\"BUS\");\n        Audio_Update();")
s=replace(s,"        md.odclk = ym.vdp.input.i_clk1;","        if (mcycles && ((mcycles & 32767) == 0)) nx_worker_progress((unsigned long long)mcycles,\"AUDIO VDP\");\n        md.odclk = ym.vdp.input.i_clk1;")

# V1.1: compare chip execution with / without the host sound sample aggregator.
# The chip clocks (YM2612, PSG) remain in the motherboard simulation; only
# Audio_Update (output mixing/decimation) is excluded for this diagnostic.
s=replace(s,'        Audio_Update();',
    '        /* V1.1: skip host sound aggregation for failure isolation. */')
s=replace(s,'        if (mcycles == 0) nx_worker_stage("W08 Audio/video update OK");',
    '        if (mcycles == 0) nx_worker_stage("W08 Video update OK");')
s=replace(s,'nx_worker_progress((unsigned long long)mcycles,"AUDIO VDP");',
    'nx_worker_progress((unsigned long long)mcycles,"VDP");')

# V1.2: Y mode isolates the video pixel rasterization, keeping
# the VDP/chip clock chain and SDL renderer running unchanged.
s=replace(s,'            Video_PlotVDP();',
  '            if (!nx_video_bypass) Video_PlotVDP();')
# V1.3: throttle host video loop and reduce SD writes
s=replace(s,'        SDL_Delay(1);', '        SDL_Delay(16);')
# Earlier debug versions wrote as many as six SD markers per 32768 clocks,
# potentially stalling the worker. Keep one milestone per interval instead.
for phase, indent in (
    ("68000","            "), ("Z80","            "),
    ("FC1004","            "), ("VRAM","            "),
    ("BUS","        "), ("VDP","        ")):
    condition = " && i == 0" if phase in ("68000","Z80","FC1004","VRAM") else ""
    line = indent + 'if (mcycles && ((mcycles & 32767) == 0)' + condition + ') nx_worker_progress((unsigned long long)mcycles,"' + phase + '");\n'
    if s.count(line) != 1: raise RuntimeError("Phase marker mismatch: "+phase)
    s=s.replace(line,'')
s=replace(s,'        mcycles++;\n        if (mcycles == 1)',
    '        mcycles++;\n        if (mcycles && ((mcycles & 32767) == 0)) nx_worker_progress((unsigned long long)mcycles,"CLOCK");\n        if (mcycles == 1)')


# V1.4 Switch-native isolation: SDL_SetWindowTitle every 16ms is unnecessary,
# invisible on Switch, and may cause a platform-specific instability.
s=replace(s,'            Video_UpdateTitle(ms);',
  '            (void)ms; /* No repeated SDL_SetWindowTitle on Switch. */')
# Distinguish a requested clean exit from an unexpected termination.
s=replace(s,'    work_thread_run = 0;\n    SDL_WaitThread(thread, 0);',
  '    nx_stage("12 Controlled shutdown");\n    work_thread_run = 0;\n    SDL_WaitThread(thread, 0);')

# V1.5: resolve confirmed fs IPC crash. Never open worker-stage.txt on the
# chip-worker thread. All SD I/O is delegated to the main thread (max 1/1.2s).
s=replace(s,'    nx_worker_stage("W00 Worker not started");',
  '    nx_worker_stage("W00 Worker not started");\n    nx_flush_worker_stage(1);')
s=replace(s,'        if (first_post_blit) { nx_stage("11a Video blit returned"); first_post_blit = 0; }',
  '        if (first_post_blit) { nx_stage("11a Video blit returned"); first_post_blit = 0; }\n        nx_flush_worker_stage(0);')

# V1.6 diagnostic: no writes to SD once the worker starts.
s=replace(s,'    nx_stage("09 Creating worker thread");',
  '    nx_stage("09 Ready: runtime SD I/O disabled");\n    nx_disable_runtime_io();')

# Main-thread read-only UI. No runtime filesystem access.
s=replace(s,"        nx_flush_worker_stage(0);","        nx_flush_worker_stage(0);\n        nx_video_show_boot(nx_get_worker_clock());")

# V1.9: sample real 68k bus activity and writes addressed to the VDP.
# Worker accumulates counts in RAM, publishes to atomic snapshot every 32768 clocks.
s=replace(s,'int SDLCALL work_thread(void *data)\n{\n    int i;',
  'int SDLCALL work_thread(void *data)\n{\n    int i;\n    unsigned long long nx_cpu_bus_cycles=0, nx_vdp_wr_cycles=0;')
s=replace(s,'            if (md.m3)\n                cart_handle_md();\n            else\n                cart_handle_m3();',
  '            if (md.m3)\n                cart_handle_md();\n            else\n                cart_handle_m3();\n            if (!m68k.o_as && !m68k.o_address_z) nx_cpu_bus_cycles++;\n            if (!md.as && !md.rw && ((md.vaddress & 0xe00000) == 0xc00000)) nx_vdp_wr_cycles++;')
s=replace(s,'        mcycles++;\n        if (mcycles && ((mcycles & 32767) == 0)) nx_worker_progress',
  '        mcycles++;\n        if (mcycles && ((mcycles & 32767) == 0)) nx_diag_capture(nx_cpu_bus_cycles,nx_vdp_wr_cycles,ym.vdp.reg_disp,md.reset);\n        if (mcycles && ((mcycles & 32767) == 0)) nx_worker_progress')

# V2.0: cross-check VDP address detection against the 68000 CPU-side bus.
s=replace(s,"    unsigned long long nx_cpu_bus_cycles=0, nx_vdp_wr_cycles=0;","    unsigned long long nx_cpu_bus_cycles=0, nx_vdp_wr_cycles=0, nx_vdp_cpu_writes=0;\n    unsigned int nx_latest_addr=0;")
s=replace(s,"            if (!m68k.o_as && !m68k.o_address_z) nx_cpu_bus_cycles++;","            if (!m68k.o_as && !m68k.o_address_z) {\n                unsigned int nx_addr=(unsigned int)m68k.o_address & 0xffffffu;\n                nx_latest_addr=nx_addr;\n                nx_cpu_bus_cycles++;\n                if (!m68k.o_rw && ((nx_addr & 0xe00000u) == 0xc00000u)) nx_vdp_cpu_writes++;\n            }")
s=replace(s,"        if (mcycles && ((mcycles & 32767) == 0)) nx_diag_capture(nx_cpu_bus_cycles,nx_vdp_wr_cycles,ym.vdp.reg_disp,md.reset);","        if (mcycles && ((mcycles & 32767) == 0)) { nx_diag_capture(nx_cpu_bus_cycles,nx_vdp_wr_cycles,ym.vdp.reg_disp,md.reset); nx_bus_publish(nx_latest_addr,nx_vdp_cpu_writes); }")
# V2.1: IMPORTANT - Nuked-MD 68000 has a 23-bit *word* address bus
# (physical CPU A1..A23), so VDP C00000 in bytes is 600000 in this bus.
# Previous 0xe00000==0xc00000 comparisons were impossible for 23-bit values.
s=replace(s,'((md.vaddress & 0xe00000) == 0xc00000)',
  '((md.vaddress & 0x700000) == 0x600000)')
s=replace(s,'((nx_addr & 0xe00000u) == 0xc00000u)',
  '((nx_addr & 0x700000u) == 0x600000u)')

# V2.2: verify VDP write acknowledge and count unique CPU bus address changes.
s=replace(s,"    unsigned int nx_latest_addr=0;","    unsigned int nx_latest_addr=0;\n    unsigned long long nx_vdp_ack_clocks=0, nx_bus_changes=0;\n    unsigned int nx_previous_addr=0xffffffffu;")
s=replace(s,"            m68k.input.i_dtack = md.dtack;","            m68k.input.i_dtack = md.dtack;\n            /* Count actual active-low acknowledge while the VDP address bus is selected. */\n            if (!md.as && !md.rw && ((md.vaddress & 0x700000)==0x600000) && !md.dtack)\n                nx_vdp_ack_clocks++;")
s=replace(s,"                nx_latest_addr=nx_addr;\n                nx_cpu_bus_cycles++;","                nx_latest_addr=nx_addr;\n                nx_cpu_bus_cycles++;\n                if (nx_addr!=nx_previous_addr) {\n                    nx_bus_changes++;\n                    nx_previous_addr=nx_addr;\n                }")
s=replace(s,"        if (mcycles && ((mcycles & 32767) == 0)) { nx_diag_capture(nx_cpu_bus_cycles,nx_vdp_wr_cycles,ym.vdp.reg_disp,md.reset); nx_bus_publish(nx_latest_addr,nx_vdp_cpu_writes); }","        if (mcycles && ((mcycles & 32767) == 0)) {\n            nx_diag_capture(nx_cpu_bus_cycles,nx_vdp_wr_cycles,ym.vdp.reg_disp,md.reset);\n            nx_bus_publish(nx_latest_addr,nx_vdp_cpu_writes);\n            /* flags: bit0 TMSS unlocked; bit1 board DTACK asserted;\n               bit2 VDP internal acknowledge; bit3 CPU bus active;\n               bit4 CPU write; bit5 CPU reset deasserted. */\n            unsigned int nxflags = (!!ym.tmss.w3)\n                | ((!md.dtack)<<1) | ((!ym.vdp.w117)<<2)\n                | ((!md.as)<<3) | ((!md.rw)<<4) | ((!!md.reset)<<5);\n            nx_ack_publish(nx_vdp_ack_clocks,nx_bus_changes,nxflags);\n        }")

# V2.4: VDP input pin diagnostics without modifying chip behavior.
s=replace(s,"    unsigned int nx_previous_addr=0xffffffffu;","    unsigned int nx_previous_addr=0xffffffffu;\n    unsigned long long nx_sel_samples=0, nx_strobe_samples=0, nx_ready_samples=0;")
s=replace(s,"            FC1004_Clock(&ym, mcycles & 1, mcycles);","            FC1004_Clock(&ym, mcycles & 1, mcycles);\n            /* Count VDP selection, byte lane strobes, and VDP-owned DTACK.\n               Evaluate only while the 68000 requests a VDP write.\n               All are read-only probes, no chip or CPU pins changed. */\n            if (!md.as && !md.rw && ((md.vaddress & 0x700000u) == 0x600000u)) {\n                if (ym.vdp.input.i_sel0 && !ym.vdp.input.i_as) {\n                    nx_sel_samples++;\n                    if (!ym.vdp.input.i_uds || !ym.vdp.input.i_lds)\n                        nx_strobe_samples++;\n                }\n                if (!ym.vdp.w117)\n                    nx_ready_samples++;\n            }")
s=replace(s,"            nx_ack_publish(nx_vdp_ack_clocks,nx_bus_changes,nxflags);","            nx_ack_publish(nx_vdp_ack_clocks,nx_bus_changes,nxflags);\n            nx_handshake_publish(nx_sel_samples,nx_strobe_samples,nx_ready_samples);")

# V2.5: probe VDP CPU interface clock, data bus, and M5 register state.
s=replace(s,"    unsigned long long nx_sel_samples=0, nx_strobe_samples=0, nx_ready_samples=0;","    unsigned long long nx_sel_samples=0, nx_strobe_samples=0, nx_ready_samples=0;\n    unsigned long long nx_clock_edges=0;\n    int nx_prev_clock0=-1;")
s=replace(s,"            FC1004_Clock(&ym, mcycles & 1, mcycles);\n            /* Count VDP selection, byte lane strobes, and VDP-owned DTACK.","            FC1004_Clock(&ym, mcycles & 1, mcycles);\n            int nx_clock0=ym.vdp.input.i_cpu_clk0;\n            if(nx_prev_clock0>=0 && nx_clock0!=nx_prev_clock0) nx_clock_edges++;\n            nx_prev_clock0=nx_clock0;\n            /* Count VDP selection, byte lane strobes, and VDP-owned DTACK.")
s=replace(s,"            nx_handshake_publish(nx_sel_samples,nx_strobe_samples,nx_ready_samples);","            nx_handshake_publish(nx_sel_samples,nx_strobe_samples,nx_ready_samples);\n            nx_vdp_state_publish(nx_clock_edges,\n                (unsigned int)(ym.vdp.io_data & 0xffffu),\n                (unsigned int)(ym.vdp.reg_m5 & 1));")
save("md.c",s)
s=load("tmss.c")
s=replace(s,'    printf("loading dummy TMSS ROM\\n");',
  '    /* No console output after the Switch ROM selector closes. */')
save("tmss.c",s)
s=load("video.c")
s=replace(s,'#include "video.h"','#include "video.h"\n#include "nx_frontend.h"')
s=replace(s,'void Video_Init(char* videoout_filename, int ntsc)','int nx_video_init(int ntsc)')
start=s.index("int nx_video_init")
end=s.index("void Video_Shutdown",start)
part=s[start:end].replace('return;','return 0;').replace('SDL_WINDOW_SHOWN','SDL_WINDOW_SHOWN | SDL_WINDOW_FULLSCREEN_DESKTOP')
part=replace(part,'    vid_dump_file = fopen(videoout_filename, "wb");','    if (!vid_texture) return 0;\n    vid_dump_file = NULL;\n    SDL_RenderSetLogicalSize(vid_renderer, 4*240, 3*240);\n    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "nearest");')
# Draw with original aspect ratio in a 4:3 logical screen. SDL letterboxes the output.
part=replace(part,'SDL_PIXELFORMAT_BGR888','SDL_PIXELFORMAT_ABGR8888')
part=replace(part,'    vid_mutex = SDL_CreateMutex();','    vid_mutex = SDL_CreateMutex();\n    return vid_mutex != NULL;')
s=s[:start]+part+s[end:]
s=replace(s,'    SDL_LockMutex(vid_mutex);\n    SDL_UpdateTexture(vid_texture, NULL, vid_currentbuffer, VID_WIDTH * 4);','    if (!vid_mutex || !vid_texture || !vid_renderer) return;\n    SDL_LockMutex(vid_mutex);\n    SDL_UpdateTexture(vid_texture, NULL, vid_currentbuffer, VID_WIDTH * 4);')
s=replace(s,'    fclose(vid_dump_file);','    if (vid_dump_file) fclose(vid_dump_file);\n    if (vid_texture) SDL_DestroyTexture(vid_texture);\n    if (vid_renderer) SDL_DestroyRenderer(vid_renderer);\n    if (vid_window) SDL_DestroyWindow(vid_window);\n    if (vid_mutex) SDL_DestroyMutex(vid_mutex);')
# V1.3: skip redundant SDL frame uploads/presents
s=replace(s,'    if (!vid_mutex || !vid_texture || !vid_renderer) return;\n    SDL_LockMutex(vid_mutex);',
'''    if (!vid_mutex || !vid_texture || !vid_renderer) return;
    static uint32_t last_presented = UINT32_MAX;
    SDL_LockMutex(vid_mutex);
    /* Present once initially, then only when a complete VDP frame arrives. */
    if (vid_counter == last_presented) {
        SDL_UnlockMutex(vid_mutex);
        return;
    }
    last_presented = vid_counter;''')

# V1.7: visible boot progress while video output remains black.
s=replace(s,"void Video_PlotVDP(void)","\n/* V1.7 boot display: no disk operations, no fonts, SDL primitives only.\n * Show progress while a genuine coloured VDP frame has not been produced. */\nstatic void nx_draw_digit(SDL_Renderer *r, int d, int x, int y, int s) {\n    static const unsigned char digit_mask[10] = {\n        0x3f,0x06,0x5b,0x4f,0x66,0x6d,0x7d,0x07,0x7f,0x6f\n    };\n    if (d < 0 || d > 9) return;\n    unsigned char mask = digit_mask[d];\n    SDL_Rect lines[7] = {\n        {x+3*s,y,12*s,2*s}, {x+15*s,y+2*s,2*s,10*s},\n        {x+15*s,y+14*s,2*s,10*s}, {x+3*s,y+24*s,12*s,2*s},\n        {x+s,y+14*s,2*s,10*s}, {x+s,y+2*s,2*s,10*s},\n        {x+3*s,y+12*s,12*s,2*s}\n    };\n    for (int i=0; i<7; i++) if (mask & (1u<<i)) SDL_RenderFillRect(r,&lines[i]);\n}\nvoid nx_video_show_boot(unsigned long long clocks) {\n    static Uint64 last_draw = 0;\n    if (!vid_renderer || !vid_mutex) return;\n    Uint64 now=SDL_GetTicks64();\n    if (last_draw && now-last_draw < 250) return;\n    last_draw=now;\n    /* Detect a non-black native VDP frame, not just a vsync counter change. */\n    int has_picture=0;\n    SDL_LockMutex(vid_mutex);\n    if (vid_counter) {\n        const uint32_t *pixels = &vid_currentbuffer[0][0];\n        for (size_t i=0; i<(size_t)VID_WIDTH*VID_HEIGHT; i+=7) {\n            if (pixels[i] & 0x00ffffffu) { has_picture=1; break; }\n        }\n    }\n    SDL_UnlockMutex(vid_mutex);\n    if (has_picture) return;\n\n    SDL_SetRenderDrawColor(vid_renderer, 7, 15, 31, 255);\n    SDL_RenderClear(vid_renderer);\n    SDL_SetRenderDrawColor(vid_renderer, 50, 125, 184, 255);\n    SDL_Rect top={74,150,812,5}, bottom={74,576,812,3};\n    SDL_RenderFillRect(vid_renderer,&top);\n    SDL_RenderFillRect(vid_renderer,&bottom);\n    SDL_SetRenderDrawColor(vid_renderer, 150, 227, 252, 255);\n    SDL_Rect bars[3]={{100,190,60,8},{170,190,60,8},{240,190,60,8}};\n    for(int i=0;i<3;i++) SDL_RenderFillRect(vid_renderer,&bars[i]);\n\n    /* Live master clock read from in-memory worker milestones. */\n    char digits[32];\n    SDL_snprintf(digits,sizeof(digits),\"%llu\",clocks);\n    int n=(int)strlen(digits), scale=3, span=n*20*scale;\n    int x=(960-span)/2;\n    if(x<18) {scale=2;span=n*20*scale;x=(960-span)/2;}\n    SDL_SetRenderDrawColor(vid_renderer, 234, 242, 250, 255);\n    for(int i=0;i<n;i++) nx_draw_digit(vid_renderer,digits[i]-'0',x+i*20*scale,300,scale);\n\n    /* A complete upstream chip-level frame is ~1,789,772 master clocks. */\n    const unsigned long long frame_clocks=1789772ULL;\n    unsigned int prog=(unsigned int)(((clocks%frame_clocks)*800ULL)/frame_clocks);\n    SDL_SetRenderDrawColor(vid_renderer, 35, 53, 71, 255);\n    SDL_Rect track={80,500,800,34};\n    SDL_RenderFillRect(vid_renderer,&track);\n    SDL_SetRenderDrawColor(vid_renderer, 77, 229, 180, 255);\n    SDL_Rect fill={80,500,(int)prog,34};\n    SDL_RenderFillRect(vid_renderer,&fill);\n    SDL_RenderPresent(vid_renderer);\n}\n\nvoid Video_PlotVDP(void)")

# V1.8: expose real vsync count and non-black pixels separately from master clocks.
s=replace(s,"void nx_video_show_boot(unsigned long long clocks) {","\n// 5x7 font for the two VDP diagnostics, drawn without file I/O or SDL_ttf.\nstatic void nx_diag_text(SDL_Renderer *r, const char *msg, int x, int y, int sz) {\n    static const struct { char ch; unsigned char rows[7]; } letters[] = {\n        {'F',{31,16,16,30,16,16,16}},\n        {'R',{30,17,17,30,20,18,17}},\n        {'A',{14,17,17,31,17,17,17}},\n        {'M',{17,27,21,21,17,17,17}},\n        {'E',{31,16,16,30,16,16,31}},\n        {'S',{15,16,16,14,1,1,30}},\n        {'P',{30,17,17,30,16,16,16}},\n        {'I',{31,4,4,4,4,4,31}},\n        {'X',{17,17,10,4,10,17,17}},\n        {'L',{16,16,16,16,16,16,31}},\n        {'C',{15,16,16,16,16,16,15}},\n        {'Y',{17,17,10,4,4,4,4}}\n    };\n    for (int k=0;msg[k];k++) {\n        for (unsigned j=0;j<sizeof(letters)/sizeof(letters[0]);j++) {\n            if (letters[j].ch != msg[k]) continue;\n            for(int yy=0;yy<7;yy++)for(int xx=0;xx<5;xx++)\n                if (letters[j].rows[yy] & (1<<(4-xx))) {\n                    SDL_Rect dot={x+(k*6+xx)*sz,y+yy*sz,sz,sz};\n                    SDL_RenderFillRect(r,&dot);\n                }\n            break;\n        }\n    }\n}\n\nvoid nx_video_show_boot(unsigned long long clocks) {")
s=replace(s,"    int has_picture=0;\n    SDL_LockMutex(vid_mutex);\n    if (vid_counter) {","    int has_picture=0;\n    unsigned int sample_pixels=0;\n    unsigned int actual_frames=0;\n    SDL_LockMutex(vid_mutex);\n    actual_frames=vid_counter;\n    if (vid_counter) {")
s=replace(s,"            if (pixels[i] & 0x00ffffffu) { has_picture=1; break; }","            if (pixels[i] & 0x00ffffffu) { has_picture=1; sample_pixels++; }")
s=replace(s,"    SDL_SetRenderDrawColor(vid_renderer, 7, 15, 31, 255);\n    SDL_RenderClear(vid_renderer);","    SDL_SetRenderDrawColor(vid_renderer, 7, 15, 31, 255);\n    SDL_RenderClear(vid_renderer);")
s=replace(s,"    /* A complete upstream chip-level frame is ~1,789,772 master clocks. */","    /* Frames count actual VDP vertical syncs, not theoretical clock division.\n       Pixels sample every seventh pixel of the latest completed VDP frame. */\n    char readout[32];\n    SDL_SetRenderDrawColor(vid_renderer, 100, 200, 230, 255);\n    nx_diag_text(vid_renderer,\"FRAMES\",115,407,3);\n    SDL_snprintf(readout,sizeof(readout),\"%u\",actual_frames);\n    for (int i=0; readout[i] && i<6;i++)\n        nx_draw_digit(vid_renderer,readout[i]-'0',112+i*32,444,1);\n    SDL_SetRenderDrawColor(vid_renderer, 100, 230, 174, 255);\n    nx_diag_text(vid_renderer,\"PIXELS\",570,407,3);\n    SDL_snprintf(readout,sizeof(readout),\"%u\",sample_pixels);\n    for (int i=0; readout[i] && i<6;i++)\n        nx_draw_digit(vid_renderer,readout[i]-'0',570+i*32,444,1);\n\n    /* A complete upstream chip-level frame is ~1,789,772 master clocks. */")

# V1.9: show raw bus reads, VDP write-level cycles, and VDP display enable state.
s=replace(s,"        {'C',{15,16,16,16,16,16,15}}",
  "        {'C',{15,16,16,16,16,16,15}},\n        {'U',{17,17,17,17,17,17,14}},\n        {'V',{17,17,17,17,17,10,4}},\n        {'D',{30,17,17,17,17,17,30}},\n        {'B',{30,17,17,30,17,17,30}},\n        {'W',{17,17,17,21,21,21,10}},\n        {'T',{31,4,4,4,4,4,4}}")
s=replace(s,'    /* A complete upstream chip-level frame is ~1,789,772 master clocks. */',
'''    unsigned long long bus=0,writes=0;
    int display=0,reset=0;
    nx_diag_read(&bus,&writes,&display,&reset);
    SDL_SetRenderDrawColor(vid_renderer, 105, 207, 238, 255);
    nx_diag_text(vid_renderer,"CPU",115,598,3);
    nx_diag_text(vid_renderer,"VDP",560,598,3);
    char status[32];
    SDL_snprintf(status,sizeof(status),"%llu",bus);
    for(int i=0;status[i] && i<9;i++)nx_draw_digit(vid_renderer,status[i]-'0',115+i*30,627,1);
    SDL_snprintf(status,sizeof(status),"%llu",writes);
    SDL_SetRenderDrawColor(vid_renderer, 121, 238, 177, 255);
    for(int i=0;status[i] && i<9;i++)nx_draw_digit(vid_renderer,status[i]-'0',560+i*30,627,1);
    /* The CPU label counts 68k active bus half-cycles, not instructions.
       The VDP label counts write-level half-cycles addressed to 0xC00000. */
    SDL_SetRenderDrawColor(vid_renderer, display?75:240, display?236:104,115,255);
    SDL_Rect disp_indicator={820,614,18,22};
    SDL_RenderFillRect(vid_renderer,&disp_indicator);
    SDL_SetRenderDrawColor(vid_renderer, reset?70:240, reset?236:104,115,255);
    SDL_Rect reset_indicator={849,614,18,22};
    SDL_RenderFillRect(vid_renderer,&reset_indicator);

    /* A complete upstream chip-level frame is ~1,789,772 master clocks. */''')

# V2.0: display last 68000 address (decimal 24-bit) and CPU-side VDP writes.
s=replace(s,"        {'C',{15,16,16,16,16,16,15}}",
    "        {'C',{15,16,16,16,16,16,15}},\n        {'D',{30,17,17,17,17,17,30}},\n        {'T',{31,4,4,4,4,4,4}}")
s=replace(s,'    /* A complete upstream chip-level frame is ~1,789,772 master clocks. */',
'''    unsigned int nxaddr=0;
    unsigned long long nxwrites=0;
    nx_bus_read(&nxaddr,&nxwrites);
    SDL_SetRenderDrawColor(vid_renderer, 148, 220, 242, 255);
    nx_diag_text(vid_renderer,"ADDR",115,668,2);
    char addrbuf[32];
    SDL_snprintf(addrbuf,sizeof(addrbuf),"%u",nxaddr);
    for(int i=0;addrbuf[i] && i<9;i++)
        nx_draw_digit(vid_renderer,addrbuf[i]-'0',115+i*30,688,1);
    SDL_SetRenderDrawColor(vid_renderer, 113, 236, 181, 255);
    nx_diag_text(vid_renderer,"DIRECT",560,668,2);
    SDL_snprintf(addrbuf,sizeof(addrbuf),"%llu",nxwrites);
    for(int i=0;addrbuf[i] && i<9;i++)
        nx_draw_digit(vid_renderer,addrbuf[i]-'0',560+i*30,688,1);

    /* A complete upstream chip-level frame is ~1,789,772 master clocks. */''')

# V2.2: display ACK and address-transition counters and status indicators.
s=replace(s,"        {'C',{15,16,16,16,16,16,15}}",
  "        {'C',{15,16,16,16,16,16,15}},\n        {'K',{17,18,20,24,20,18,17}},\n        {'O',{14,17,17,17,17,17,14}},\n        {'N',{17,25,21,19,17,17,17}}")
s=replace(s,'    /* A complete upstream chip-level frame is ~1,789,772 master clocks. */',
'''    unsigned long long ack_clocks=0, bus_changes=0;
    unsigned int ack_flags=0;
    nx_ack_read(&ack_clocks,&bus_changes,&ack_flags);
    SDL_SetRenderDrawColor(vid_renderer, 158, 210, 237, 255);
    nx_diag_text(vid_renderer,"ACK",115,217,3);
    nx_diag_text(vid_renderer,"MOVES",390,217,3);
    nx_diag_text(vid_renderer,"TMSS",732,217,3);
    char ckbuf[32];
    SDL_snprintf(ckbuf,sizeof(ckbuf),"%llu",ack_clocks);
    for(int i=0;ckbuf[i] && i<8;i++)
        nx_draw_digit(vid_renderer,ckbuf[i]-'0',115+i*30,248,1);
    SDL_snprintf(ckbuf,sizeof(ckbuf),"%llu",bus_changes);
    for(int i=0;ckbuf[i] && i<8;i++)
        nx_draw_digit(vid_renderer,ckbuf[i]-'0',390+i*30,248,1);
    SDL_SetRenderDrawColor(vid_renderer,(ack_flags&1)?62:228,(ack_flags&1)?224:94,105,255);
    SDL_Rect tmsslamp={746,252,22,21};
    SDL_RenderFillRect(vid_renderer,&tmsslamp);
    SDL_SetRenderDrawColor(vid_renderer,(ack_flags&2)?62:228,(ack_flags&2)?224:94,105,255);
    SDL_Rect acklamp={781,252,22,21};
    SDL_RenderFillRect(vid_renderer,&acklamp);
    SDL_SetRenderDrawColor(vid_renderer,(ack_flags&4)?62:228,(ack_flags&4)?224:94,105,255);
    SDL_Rect vdpacklamp={816,252,22,21};
    SDL_RenderFillRect(vid_renderer,&vdpacklamp);

    /* A complete upstream chip-level frame is ~1,789,772 master clocks. */''')

# V2.4: pin-level handshake probes above the existing first bar.
s=replace(s,'    /* A complete upstream chip-level frame is ~1,789,772 master clocks. */',
'''    unsigned long long vsel=0,vstrobe=0,vready=0;
    nx_handshake_read(&vsel,&vstrobe,&vready);
    SDL_SetRenderDrawColor(vid_renderer, 128, 216, 235, 255);
    nx_diag_text(vid_renderer,"SEL",102,41,3);
    nx_diag_text(vid_renderer,"STB",389,41,3);
    nx_diag_text(vid_renderer,"RDY",681,41,3);
    char pinbuf[32];
    SDL_snprintf(pinbuf,sizeof(pinbuf),"%llu",vsel);
    for(int i=0;pinbuf[i] && i<9;i++) nx_draw_digit(vid_renderer,pinbuf[i]-'0',102+i*28,73,1);
    SDL_snprintf(pinbuf,sizeof(pinbuf),"%llu",vstrobe);
    for(int i=0;pinbuf[i] && i<9;i++) nx_draw_digit(vid_renderer,pinbuf[i]-'0',389+i*28,73,1);
    SDL_snprintf(pinbuf,sizeof(pinbuf),"%llu",vready);
    for(int i=0;pinbuf[i] && i<9;i++) nx_draw_digit(vid_renderer,pinbuf[i]-'0',681+i*28,73,1);

    /* A complete upstream chip-level frame is ~1,789,772 master clocks. */''')

# V2.5: display clock transitions, VDP data bus, and internal M5 register bit.
s=replace(s,"    /* A complete upstream chip-level frame is ~1,789,772 master clocks. */","    /* V2.5 pin state: actual CPU clock transitions, VDP data bus, M5 mode. */\n    unsigned long long vdpclk=0;\n    unsigned int vdpdata=0, vdpmode=0;\n    nx_vdp_state_read(&vdpclk,&vdpdata,&vdpmode);\n    SDL_SetRenderDrawColor(vid_renderer, 128, 216, 235, 255);\n    nx_diag_text(vid_renderer,\"CLK\",102,102,2);\n    nx_diag_text(vid_renderer,\"DATA\",385,102,2);\n    nx_diag_text(vid_renderer,\"MODE\",688,102,2);\n    char diagbuf[32];\n    SDL_snprintf(diagbuf,sizeof(diagbuf),\"%llu\",vdpclk);\n    for(int i=0;diagbuf[i] && i<8;i++) nx_draw_digit(vid_renderer,diagbuf[i]-'0',102+i*27,119,1);\n    SDL_snprintf(diagbuf,sizeof(diagbuf),\"%u\",vdpdata);\n    for(int i=0;diagbuf[i] && i<6;i++) nx_draw_digit(vid_renderer,diagbuf[i]-'0',385+i*27,119,1);\n    nx_draw_digit(vid_renderer,(int)(vdpmode&1u),688,119,1);\n\n    /* A complete upstream chip-level frame is ~1,789,772 master clocks. */")
save("video.c",s)
# Redecimate() logs to stdout, which can be detached on Switch; silence the log.
s=load("audio.c")
s=replace(s,'\tprintf("Audio sample rate: %d, SoundCard sample rate: %d, decimate factor: %d\\n", SampleRate, OutputSampleRate, DecimateEach);',
  '\t/* Avoid writes to stdout after closing the Switch ROM selector console. */')
start=s.index("static void SoundOutput_Mixer")
end=s.index("static void FeedSampleForDump",start)
s=s[:start]+'''/* Host audio adapter: preserves FM/PSG mixer below, eliminates disk dumps. */
static SDL_AudioStream *nx_audio_stream;
static int16_t nx_samples[512*2];
static unsigned nx_count;

void Audio_Init(char* audioout_filename, int ntsc)
{
    (void)audioout_filename;
    audio_out = NULL;
    Redecimate(ntsc);
    nx_count = 0;
    if (SDL_InitSubSystem(SDL_INIT_AUDIO) < 0) return;
    SDL_zero(spec);
    spec.freq = 48000;
    spec.format = AUDIO_S16SYS;
    spec.channels = 2;
    spec.samples = 1024;
    dev_id = SDL_OpenAudioDevice(NULL, 0, &spec, &spec_obtainted, 0);
    if (!dev_id) return;
    nx_audio_stream = SDL_NewAudioStream(AUDIO_S16SYS, 2, OutputSampleRate,
        spec_obtainted.format, spec_obtainted.channels, spec_obtainted.freq);
    if (!nx_audio_stream) { SDL_CloseAudioDevice(dev_id); dev_id = 0; return; }
    SDL_PauseAudioDevice(dev_id, 0);
}
void Audio_Shutdown(void)
{
    if (dev_id) SDL_CloseAudioDevice(dev_id);
    if (nx_audio_stream) SDL_FreeAudioStream(nx_audio_stream);
    SDL_QuitSubSystem(SDL_INIT_AUDIO);
}
static void FeedSampleForPlayback(int l, int r)
{
    if (++DecimateCounter < DecimateEach) return;
    DecimateCounter=0;
    if (!dev_id || !nx_audio_stream) return;
    nx_samples[2*nx_count]=l; nx_samples[2*nx_count+1]=r;
    if (++nx_count < 512) return;
    nx_count=0;
    if (SDL_AudioStreamPut(nx_audio_stream,nx_samples,sizeof(nx_samples)) < 0) return;
    int16_t output[2048];
    int n;
    while ((n=SDL_AudioStreamGet(nx_audio_stream,output,sizeof(output)))>0) {
        /* Bound latency without blocking shutdown or changing chip clocks. */
        if (SDL_GetQueuedAudioSize(dev_id) > 48000*4/4) SDL_ClearQueuedAudio(dev_id);
        SDL_QueueAudio(dev_id,output,n);
    }
}

'''+s[end:]
s=replace(s,'\t\tFeedSampleForDump(suml, sumr);','\t\t/* No diagnostic dump on the SD card. */')
save("audio.c",s)

# Built-in original diagnostic cartridge, no SD access necessary.
s=load("cartridge.c")
s=replace(s,'#include "savestate.h"','#include "savestate.h"\n#include "diagnostic_rom.h"'.replace('\n','\n'))
s=replace(s,'    romfile = fopen(filename, "rb");','''    if (!strcmp(filename, "builtin:diagnostic")) {
        mapper_enable = 0;
        m3_mapper_enable = 0;
        memset(rom, 0, sizeof(rom));
        memcpy(rom, diagnostic_rom, sizeof(diagnostic_rom));
        for (i = 0; i < ROM_SIZE * 2; i++) rom[i] = short_swap(rom[i]);
        return 0;
    }
    romfile = fopen(filename, "rb");''')

# Fine-grained checkpoints: a user can see the last successful cartridge step.
s=replace(s,'#include "diagnostic_rom.h"',
  '#include "diagnostic_rom.h"\n#include "nx_frontend.h"')
s=replace(s,'    romfile = fopen(filename, "rb");',
  '    nx_stage("03a ROM opening");\n    romfile = fopen(filename, "rb");')
s=replace(s,'    fseek(romfile, 0, SEEK_END);',
  '    nx_stage("03b ROM file opened");\n    fseek(romfile, 0, SEEK_END);')
s=replace(s,'    rewind(romfile);',
  '    rewind(romfile);\n    nx_stage("03c ROM size read");')
s=replace(s,'    memset(rom, 0, sizeof(rom));\n    ret = fread(rom, 1, siz, romfile);',
  '    nx_stage("03d Clearing ROM buffer");\n    memset(rom, 0, sizeof(rom));\n    nx_stage("03e Reading ROM data");\n    ret = fread(rom, 1, siz, romfile);')
s=replace(s,'    for (i = 0; i < ROM_SIZE * 2; i++)\n        rom[i] = short_swap(rom[i]);',
  '    nx_stage("03f ROM data loaded");\n    for (i = 0; i < ROM_SIZE * 2; i++)\n        rom[i] = short_swap(rom[i]);\n    nx_stage("03g ROM conversion done");')
save("cartridge.c",s)
