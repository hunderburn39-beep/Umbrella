/* Umbrella NX frontend, GPL-2.0-or-later. */
#include <switch.h>
#include <SDL.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <dirent.h>
#include <stdlib.h>
#include "controller.h"
#include "nx_frontend.h"
#define ROOT "sdmc:/switch/Umbrella-MegaDrive-NX/"
#define ROMS ROOT "roms/"
/* Enable isolated raster test from the ROM selector via Y. */
int nx_video_bypass = 0;
/* V1.6: disable filesystem IPC once simulation starts. */
static int nx_runtime_io_blocked = 0;
void nx_disable_runtime_io(void) {
    __atomic_store_n(&nx_runtime_io_blocked, 1, __ATOMIC_RELEASE);
}
/* Setup marker written before simulation only. */
void nx_stage(const char *step) {
    if (__atomic_load_n(&nx_runtime_io_blocked, __ATOMIC_ACQUIRE)) return;
    FILE *f = fopen(ROOT "last-stage.txt", "wb");
    if (f) { fprintf(f, "%s\n", step); fclose(f); }
}
/* Native worker must never issue filesystem IPC. Main thread flushes snapshots. */
static const char *worker_label = "W00 Not started";
static const char *worker_phase = "CLOCK";
static unsigned long long worker_clock = 0;
static int worker_progress_mode = 0;
void nx_worker_stage(const char *step) {
    __atomic_store_n(&worker_label, step, __ATOMIC_RELEASE);
    __atomic_store_n(&worker_progress_mode, 0, __ATOMIC_RELEASE);
}
void nx_worker_progress(unsigned long long clock, const char *phase) {
    __atomic_store_n(&worker_clock, clock, __ATOMIC_RELEASE);
    __atomic_store_n(&worker_phase, phase, __ATOMIC_RELEASE);
    __atomic_store_n(&worker_progress_mode, 1, __ATOMIC_RELEASE);
}
/* Read-only shared snapshots, published every 32768 master clocks. */
static unsigned long long nx_bus_reads = 0, nx_vdp_write_cycles = 0;
static int nx_vdp_disp = 0;
static int nx_chip_reset = 0;
void nx_diag_capture(unsigned long long bus_reads,
                     unsigned long long vdp_writes,int vdp_disp,int chip_reset) {
    __atomic_store_n(&nx_bus_reads,bus_reads,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_vdp_write_cycles,vdp_writes,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_vdp_disp,vdp_disp,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_chip_reset,chip_reset,__ATOMIC_RELEASE);
}
void nx_diag_read(unsigned long long *reads,unsigned long long *writes,
                  int *display,int *reset) {
    *reads=__atomic_load_n(&nx_bus_reads,__ATOMIC_ACQUIRE);
    *writes=__atomic_load_n(&nx_vdp_write_cycles,__ATOMIC_ACQUIRE);
    *display=__atomic_load_n(&nx_vdp_disp,__ATOMIC_ACQUIRE);
    *reset=__atomic_load_n(&nx_chip_reset,__ATOMIC_ACQUIRE);
}
/* Clock worker snapshots. Never performs filesystem I/O. */
static unsigned int nx_last_cpu_address = 0;
static unsigned long long nx_direct_vdp_writes = 0;
void nx_bus_publish(unsigned int address,unsigned long long direct_writes) {
    __atomic_store_n(&nx_last_cpu_address,address,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_direct_vdp_writes,direct_writes,__ATOMIC_RELEASE);
}
void nx_bus_read(unsigned int *address,unsigned long long *direct_writes) {
    *address=__atomic_load_n(&nx_last_cpu_address,__ATOMIC_ACQUIRE);
    *direct_writes=__atomic_load_n(&nx_direct_vdp_writes,__ATOMIC_ACQUIRE);
}
/* V2.2: independent DTACK/bus-transition snapshots. No runtime I/O. */
static unsigned long long nx_vdp_ack_clocks = 0, nx_cpu_bus_changes = 0;
static unsigned int nx_bus_flags = 0;
void nx_ack_publish(unsigned long long ack,unsigned long long changes,unsigned int flags) {
    __atomic_store_n(&nx_vdp_ack_clocks,ack,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_cpu_bus_changes,changes,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_bus_flags,flags,__ATOMIC_RELEASE);
}
void nx_ack_read(unsigned long long *ack,unsigned long long *changes,unsigned int *flags) {
    *ack=__atomic_load_n(&nx_vdp_ack_clocks,__ATOMIC_ACQUIRE);
    *changes=__atomic_load_n(&nx_cpu_bus_changes,__ATOMIC_ACQUIRE);
    *flags=__atomic_load_n(&nx_bus_flags,__ATOMIC_ACQUIRE);
}
unsigned long long nx_get_worker_clock(void) {
    return __atomic_load_n(&worker_clock, __ATOMIC_ACQUIRE);
}
/* Called ONLY from the main SDL loop, never from the chip clock worker. */
void nx_flush_worker_stage(int force) {
    if (__atomic_load_n(&nx_runtime_io_blocked, __ATOMIC_ACQUIRE)) return;
    static u64 initial_tick=0, last_flush_tick=0;
    static char last_saved[128] = "";
    u64 now = SDL_GetTicks64();
    if (!initial_tick) initial_tick = now;
    if (!force && (now - last_flush_tick < 1200)) return;
    last_flush_tick = now;
    const int mode = __atomic_load_n(&worker_progress_mode, __ATOMIC_ACQUIRE);
    char buf[128];
    if (mode) {
        unsigned long long clock = __atomic_load_n(&worker_clock, __ATOMIC_ACQUIRE);
        const char *phase = __atomic_load_n(&worker_phase, __ATOMIC_ACQUIRE);
        snprintf(buf,sizeof(buf),"C%llu %s%s T%llus",clock,phase,
                 nx_video_bypass ? " NR" : "",(unsigned long long)((now-initial_tick)/1000));
    } else {
        const char *label=__atomic_load_n(&worker_label, __ATOMIC_ACQUIRE);
        snprintf(buf,sizeof(buf),"%s",label);
    }
    if (!force && strcmp(buf,last_saved)==0) return;
    FILE *out = fopen(ROOT "worker-stage.txt","wb");
    if(out) {
        fputs(buf,out);
        fputc('\n',out);
        fclose(out);
        snprintf(last_saved,sizeof(last_saved),"%s",buf);
    }
}
static void nx_previous_worker_stage(char *out, size_t cap) {
    snprintf(out, cap, "%s", "No worker run recorded");
    FILE *f = fopen(ROOT "worker-stage.txt", "rb");
    if (!f) return;
    if (fgets(out, cap, f)) out[strcspn(out, "\r\n")] = 0;
    fclose(f);
}
static void nx_previous_stage(char *out, size_t cap) {
    snprintf(out, cap, "%s", "No previous startup recorded");
    FILE *f = fopen(ROOT "last-stage.txt", "rb");
    if (!f) return;
    if (fgets(out, cap, f)) out[strcspn(out, "\r\n")] = 0;
    fclose(f);
}
static PadState pad;
static char chosen[512];
static char names[128][256];
static int compare(const void *a,const void *b) {return strcasecmp(a,b);}
void nx_pad_init(void) {
    padConfigureInput(1,HidNpadStyleSet_NpadStandard);
    padInitializeDefault(&pad);
}
void nx_error(const char *message) {
    consoleInit(NULL);
    nx_pad_init();
    printf("Umbrella Mega Drive NX\n\n%s\n\nPress B or + to exit.\n",message);
    while(appletMainLoop()) {
        padUpdate(&pad);
        if(padGetButtonsDown(&pad)&(HidNpadButton_B|HidNpadButton_Plus)) break;
        consoleUpdate(NULL);
    }
    consoleExit(NULL);
}
int nx_choose_rom(char **rom) {
    /* A command-line path takes priority; otherwise present a native ROM list. */
    if(strcmp(*rom,ROOT "rom.bin")!=0) return 1;
    int count=0,selected=0,ok=0;
    char previous[128];
    nx_previous_stage(previous, sizeof(previous));
    char previous_worker[128];
    nx_previous_worker_stage(previous_worker, sizeof(previous_worker));
    DIR *d=opendir(ROMS);
    if(d) {
        struct dirent *e;
        while((e=readdir(d)) && count<128) {
            const char *ext=strrchr(e->d_name,'.');
            if(ext && (!strcasecmp(ext,".bin")||!strcasecmp(ext,".md")||!strcasecmp(ext,".gen"))
                && strlen(e->d_name)<sizeof(names[0])) {
                strcpy(names[count++],e->d_name);
            }
        }
        closedir(d);
    }
    if(!count) {
        FILE *f=fopen(*rom,"rb");
        if(f) { fclose(f); return 1; }
        *rom = "builtin:diagnostic";
        return 1;
    }
    qsort(names,count,sizeof(names[0]),compare);
    consoleInit(NULL); nx_pad_init();
    while(appletMainLoop()) {
        padUpdate(&pad);
        u64 b=padGetButtonsDown(&pad);
        if(b&HidNpadButton_Up) selected=(selected+count-1)%count;
        if(b&HidNpadButton_Down) selected=(selected+1)%count;
        if(b&HidNpadButton_B) break;
        if(b&HidNpadButton_X) { *rom="builtin:diagnostic"; ok=1; break; }
        if(b&(HidNpadButton_A|HidNpadButton_Y)) {
            nx_video_bypass = !!(b&HidNpadButton_Y);
            snprintf(chosen,sizeof(chosen),"%s%s",ROMS,names[selected]);
            *rom=chosen;ok=1;break;
        }
        printf("\x1b[2J\x1b[HUmbrella Mega Drive NX V2.2\nChip-level simulation\n\n");
        int first=(selected/12)*12;
        for(int i=first;i<count && i<first+12;i++) printf("%c %.60s\n",i==selected?'>':' ',names[i]);
        printf("\nA: normal  Y: no raster\nX: diagnostic  B: exit\nLast stage: %.80s\nWorker stage: %.80s\nV2.2: DTACK and stalled write diagnosis\n",previous,previous_worker);
        consoleUpdate(NULL);
    }
    consoleExit(NULL);return ok;
}
int nx_pad_poll(void) {
    padUpdate(&pad);
    u64 held=padGetButtons(&pad);
    u64 down=padGetButtonsDown(&pad);
    static const struct {u64 mask;int key;} map[]={
        {HidNpadButton_Up,SDL_SCANCODE_UP},{HidNpadButton_Down,SDL_SCANCODE_DOWN},
        {HidNpadButton_Left,SDL_SCANCODE_LEFT},{HidNpadButton_Right,SDL_SCANCODE_RIGHT},
        {HidNpadButton_Y,SDL_SCANCODE_Z},{HidNpadButton_B,SDL_SCANCODE_X},
        {HidNpadButton_A,SDL_SCANCODE_C},{HidNpadButton_Plus,SDL_SCANCODE_RETURN}
    };
    HidAnalogStickState stick=padGetStickPos(&pad,0);
    if(stick.x>16000) held|=HidNpadButton_Right;
    if(stick.x< -16000) held|=HidNpadButton_Left;
    if(stick.y>16000) held|=HidNpadButton_Up;
    if(stick.y< -16000) held|=HidNpadButton_Down;
    for(unsigned i=0;i<sizeof(map)/sizeof(map[0]);i++)
        controller_sdl_event(map[i].key,!!(held&map[i].mask));
    return !!(down&HidNpadButton_Minus);
}
