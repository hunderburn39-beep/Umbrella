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
save("md.c",s)
s=load("tmss.c")
s=replace(s,'    printf("loading dummy TMSS ROM\\n");',
  '    /* No console output after the Switch ROM selector closes. */')
save("tmss.c",s)
s=load("video.c")
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
