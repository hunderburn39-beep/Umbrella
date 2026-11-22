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
/* Crash marker persists after the Switch closes the executable. */
void nx_stage(const char *step) {
    FILE *f = fopen(ROOT "last-stage.txt", "wb");
    if (f) { fprintf(f, "%s\n", step); fclose(f); }
}
/* Worker has its own marker file, never overwritten by the video thread. */
void nx_worker_stage(const char *step) {
    FILE *f = fopen(ROOT "worker-stage.txt", "wb");
    if (f) { fprintf(f, "%s\n", step); fclose(f); }
}
void nx_worker_progress(unsigned long long clock, const char *phase) {
    char buf[112];
    static u64 first_tick = 0;
    u64 tick = armGetSystemTick();
    if (!first_tick) first_tick = tick;
    u64 elapsed_s = armTicksToNs(tick - first_tick) / 1000000000ULL;
    snprintf(buf, sizeof(buf), "C%llu %s%s T%llus",
             clock, phase, nx_video_bypass ? " NR" : "", (unsigned long long)elapsed_s);
    nx_worker_stage(buf);
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
        printf("\x1b[2J\x1b[HUmbrella Mega Drive NX V1.3\nChip-level simulation\n\n");
        int first=(selected/12)*12;
        for(int i=first;i<count && i<first+12;i++) printf("%c %.60s\n",i==selected?'>':' ',names[i]);
        printf("\nA: normal  Y: no raster\nX: diagnostic  B: exit\nLast stage: %.80s\nWorker stage: %.80s\n",previous,previous_worker);
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
