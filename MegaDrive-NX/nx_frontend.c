/* Umbrella NX frontend, GPL-2.0-or-later. */
#include <switch.h>
#include <switch/services/clkrst.h>
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
/* Hardware jumpers: 0 JP/NTSC, 1 export/NTSC, 2 export/PAL.
 * The original Nuked-MD i_jap signal is active low. */
int nx_region_setting = 0;
/* Keeps bus telemetry visible even after the VDP produces a coloured image.
 * Toggle with L during simulation, never changes the chip logic. */
int nx_show_hud = 1;
/* ZL: omit optional high-frequency VDP diagnostic probes, not chip clocks. */
int nx_light_probes = 0;
/* V3.4: best-effort official clock service; never assume elevated rights. */
static ClkrstSession nx_cpu_session;
static int nx_cpu_clock_open = 0;
static u32 nx_cpu_original_hz = 0;
static u32 nx_cpu_observed_hz = 0;
static int nx_cpu_clock_status = 0;
void nx_cpu_boost_start(void) {
    nx_cpu_clock_status=0;
    if (R_FAILED(clkrstInitialize())) { nx_cpu_clock_status=-1; return; }
    if (R_FAILED(clkrstOpenSession(&nx_cpu_session,PcvModuleId_CpuBus,3))) {
        nx_cpu_clock_status=-2;
        clkrstExit();
        return;
    }
    nx_cpu_clock_open=1;
    if (R_FAILED(clkrstGetClockRate(&nx_cpu_session,&nx_cpu_original_hz))) {
        nx_cpu_clock_status=-3;
        return;
    }
    nx_cpu_observed_hz=nx_cpu_original_hz;
    /* Conservative request: 1.224 GHz. May be denied by firmware/CFW.
       No voltage control, no GPU or memory overclock, no repeated retries. */
    if (R_FAILED(clkrstSetClockRate(&nx_cpu_session,1224000000u))) {
        nx_cpu_clock_status=-4;
        return;
    }
    if (R_FAILED(clkrstGetClockRate(&nx_cpu_session,&nx_cpu_observed_hz))) {
        nx_cpu_clock_status=-5;
        return;
    }
    nx_cpu_clock_status=(nx_cpu_observed_hz>=1224000000u)?1:2;
}
void nx_cpu_boost_stop(void) {
    if (nx_cpu_clock_open) {
        if (nx_cpu_original_hz) clkrstSetClockRate(&nx_cpu_session,nx_cpu_original_hz);
        clkrstCloseSession(&nx_cpu_session);
        nx_cpu_clock_open=0;
        clkrstExit();
    }
}
void nx_cpu_boost_info(unsigned int *hz,int *status) {
    *hz=nx_cpu_observed_hz;
    *status=nx_cpu_clock_status;
}
static const char *nx_region_names[] = {
    "Japan (NTSC 60Hz)", "USA (NTSC 60Hz)", "Europe (PAL 50Hz)"
};
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
/* V2.4 VDP input handshake counters; worker-only writer, UI-only reader. */
static unsigned long long nx_vdp_sel_samples=0, nx_vdp_strobe_samples=0, nx_vdp_ready_samples=0;
void nx_handshake_publish(unsigned long long sel,unsigned long long strobe,unsigned long long ready) {
    __atomic_store_n(&nx_vdp_sel_samples,sel,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_vdp_strobe_samples,strobe,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_vdp_ready_samples,ready,__ATOMIC_RELEASE);
}
void nx_handshake_read(unsigned long long *sel,unsigned long long *strobe,unsigned long long *ready) {
    *sel=__atomic_load_n(&nx_vdp_sel_samples,__ATOMIC_ACQUIRE);
    *strobe=__atomic_load_n(&nx_vdp_strobe_samples,__ATOMIC_ACQUIRE);
    *ready=__atomic_load_n(&nx_vdp_ready_samples,__ATOMIC_ACQUIRE);
}
/* V2.5: capture internal VDP CPU-clock transitions and ROM register writes.
   These are atomic in-memory snapshots, never saved to SD while running. */
static unsigned long long nx_vdp_clock_edges = 0;
static unsigned int nx_vdp_last_data = 0, nx_vdp_mode_m5 = 0;
void nx_vdp_state_publish(unsigned long long edges,unsigned int data,unsigned int mode) {
    __atomic_store_n(&nx_vdp_clock_edges,edges,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_vdp_last_data,data,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_vdp_mode_m5,mode,__ATOMIC_RELEASE);
}
void nx_vdp_state_read(unsigned long long *edges,unsigned int *data,unsigned int *mode) {
    *edges=__atomic_load_n(&nx_vdp_clock_edges,__ATOMIC_ACQUIRE);
    *data=__atomic_load_n(&nx_vdp_last_data,__ATOMIC_ACQUIRE);
    *mode=__atomic_load_n(&nx_vdp_mode_m5,__ATOMIC_ACQUIRE);
}
/* V2.6 VDP command decode stages (sampled by the chip worker, no I/O). */
static unsigned long long nx_decode_count=0, nx_gate_count=0, nx_ctrl_count=0;
void nx_decode_publish(unsigned long long decode,unsigned long long gate,unsigned long long ctrl) {
    __atomic_store_n(&nx_decode_count,decode,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_gate_count,gate,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_ctrl_count,ctrl,__ATOMIC_RELEASE);
}
void nx_decode_read(unsigned long long *decode,unsigned long long *gate,unsigned long long *ctrl) {
    *decode=__atomic_load_n(&nx_decode_count,__ATOMIC_ACQUIRE);
    *gate=__atomic_load_n(&nx_gate_count,__ATOMIC_ACQUIRE);
    *ctrl=__atomic_load_n(&nx_ctrl_count,__ATOMIC_ACQUIRE);
}
/* V2.7: original 68000 data-output visibility for VDP command handshake. */
static unsigned long long nx_drive_clocks=0;
static unsigned int nx_drive_word=0;
void nx_drive_publish(unsigned long long clocks,unsigned int word) {
    __atomic_store_n(&nx_drive_clocks,clocks,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_drive_word,word,__ATOMIC_RELEASE);
}
void nx_drive_read(unsigned long long *clocks,unsigned int *word) {
    *clocks=__atomic_load_n(&nx_drive_clocks,__ATOMIC_ACQUIRE);
    *word=__atomic_load_n(&nx_drive_word,__ATOMIC_ACQUIRE);
}
/* V2.9 VDP internal command/acknowledge gate samples. */
static unsigned long long nx_pipe_cmd=0,nx_pipe_gate=0,nx_pipe_req=0;
void nx_pipe_publish(unsigned long long cmd,unsigned long long gate,unsigned long long req) {
    __atomic_store_n(&nx_pipe_cmd,cmd,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_pipe_gate,gate,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_pipe_req,req,__ATOMIC_RELEASE);
}
void nx_pipe_read(unsigned long long *cmd,unsigned long long *gate,unsigned long long *req) {
    *cmd=__atomic_load_n(&nx_pipe_cmd,__ATOMIC_ACQUIRE);
    *gate=__atomic_load_n(&nx_pipe_gate,__ATOMIC_ACQUIRE);
    *req=__atomic_load_n(&nx_pipe_req,__ATOMIC_ACQUIRE);
}
/* V3.0: experimental one-shot VDP DTACK pulse, ZR only.
 * Requests originate on the main controller thread; the worker decides
 * if the active CPU cycle qualifies. No file operations. */
static int nx_skip_requested=0;
static int nx_skip_status=0; /* 0=idle 1=requested 2=pulsing 3=advanced 4=timeout 5=not eligible */
static unsigned int nx_skip_tries=0;
void nx_skip_request(void) {
    __atomic_store_n(&nx_skip_requested,1,__ATOMIC_RELEASE);
    __atomic_store_n(&nx_skip_status,1,__ATOMIC_RELEASE);
}
int nx_skip_take(void) {
    return __atomic_exchange_n(&nx_skip_requested,0,__ATOMIC_ACQ_REL);
}
void nx_skip_report(int status) {
    if(status==2) __atomic_add_fetch(&nx_skip_tries,1,__ATOMIC_ACQ_REL);
    __atomic_store_n(&nx_skip_status,status,__ATOMIC_RELEASE);
}
void nx_skip_read(unsigned int *tries,int *status) {
    *tries=__atomic_load_n(&nx_skip_tries,__ATOMIC_ACQUIRE);
    *status=__atomic_load_n(&nx_skip_status,__ATOMIC_ACQUIRE);
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

/* V3.5 native 1280x720 sky-blue graphical launcher. GPU-backed SDL2 renderer.
   Pure frontend: the chip simulation is not modified. */
static const unsigned char nx_font[37][7]={
{14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{15,16,16,16,16,16,15},
{30,17,17,17,17,17,30},{31,16,16,30,16,16,31},{31,16,16,30,16,16,16},
{15,16,16,19,17,17,15},{17,17,17,31,17,17,17},{31,4,4,4,4,4,31},
{7,2,2,2,18,18,12},{17,18,20,24,20,18,17},{16,16,16,16,16,16,31},
{17,27,21,21,17,17,17},{17,25,21,19,17,17,17},{14,17,17,17,17,17,14},
{30,17,17,30,16,16,16},{14,17,17,17,21,18,13},{30,17,17,30,20,18,17},
{15,16,16,14,1,1,30},{31,4,4,4,4,4,4},{17,17,17,17,17,17,14},
{17,17,17,17,17,10,4},{17,17,17,21,21,21,10},{17,17,10,4,10,17,17},
{17,17,10,4,4,4,4},{31,1,2,4,8,16,31},
{14,17,19,21,25,17,14},{4,12,4,4,4,4,14},{14,17,1,2,4,8,31},
{30,1,1,14,1,1,30},{2,6,10,18,31,2,2},{31,16,16,30,1,1,30},
{14,16,16,30,17,17,14},{31,1,2,4,8,8,8},
{14,17,17,14,17,17,14},{14,17,17,15,1,1,14},
{0,0,0,0,0,0,0}
};
static void nx_ui_text(SDL_Renderer *r,const char *str,int x,int y,int scale,
                       Uint8 red,Uint8 green,Uint8 blue) {
    SDL_SetRenderDrawColor(r,red,green,blue,255);
    for(int i=0;str[i] && i<64;i++) {
        unsigned char c=(unsigned char)str[i];
        if(c>='a' && c<='z') c-=32;
        int idx=c>='A'&&c<='Z'?c-'A':c>='0'&&c<='9'?26+c-'0':36;
        for(int row=0;row<7;row++)
            for(int col=0;col<5;col++) if(nx_font[idx][row]&(16>>col)) {
                SDL_Rect px={x+i*6*scale+col*scale,y+row*scale,scale,scale};
                SDL_RenderFillRect(r,&px);
            }
    }
}
static void nx_ui_box(SDL_Renderer *r,int x,int y,int w,int h,
                      Uint8 red,Uint8 green,Uint8 blue) {
    SDL_SetRenderDrawColor(r,red,green,blue,255);
    SDL_Rect rect={x,y,w,h};
    SDL_RenderFillRect(r,&rect);
}
static void nx_ui_draw(SDL_Renderer *r,int count,int selected) {
    /* Sky-blue gradient rendered with GPU fill commands. */
    for(int y=0;y<720;y+=8) {
        int t=y/8;
        nx_ui_box(r,0,y,1280,8,(Uint8)(94+t/3),(Uint8)(188+t/5),
                  (Uint8)(245-t/7));
    }
    nx_ui_box(r,0,0,1280,102,25,105,180);
    nx_ui_text(r,"UMBRELLA MEGA DRIVE NX",75,24,5,255,255,255);
    nx_ui_text(r,"CHIP LEVEL ENGINE",80,73,2,183,235,255);
    nx_ui_box(r,70,135,740,475,233,248,255);
    nx_ui_text(r,"SELECIONAR JOGO",105,160,3,25,97,157);
    int first=(selected/8)*8;
    for(int i=first;i<count && i<first+8;i++) {
        int y=210+(i-first)*46;
        nx_ui_box(r,95,y,690,41,i==selected?31:205,
                  i==selected?149:233,i==selected?105:246);
        char title[50];
        snprintf(title,sizeof(title),"%.37s",names[i]);
        nx_ui_text(r,title,112,y+10,2,i==selected?255:32,
                   i==selected?255:88,i==selected?255:129);
    }
    nx_ui_box(r,845,135,360,475,233,248,255);
    nx_ui_text(r,"REGIAO",882,163,3,25,97,157);
    const char *regions[]={"JAPAO 60HZ","EUA 60HZ","EUROPA 50HZ"};
    for(int i=0;i<3;i++) {
        int y=215+i*65;
        nx_ui_box(r,869,y,313,52,i==nx_region_setting?32:167,
                  i==nx_region_setting?167:208,i==nx_region_setting?99:229);
        nx_ui_text(r,regions[i],890,y+15,2,i==nx_region_setting?255:27,
                   i==nx_region_setting?255:97,i==nx_region_setting?255:142);
    }
    nx_ui_box(r,870,440,312,76,21,164,84);
    nx_ui_text(r,"EXECUTAR  A",896,462,3,255,255,255);
    nx_ui_box(r,870,531,312,55,31,136,182);
    nx_ui_text(r,"DIAGNOSTICO X",893,550,2,255,255,255);
    nx_ui_box(r,0,636,1280,84,25,105,180);
    nx_ui_text(r,"CIMA BAIXO JOGO    L R REGIAO    B SAIR",65,660,2,255,255,255);
    nx_ui_text(r,"V3 5",1100,660,2,255,255,255);
    SDL_RenderPresent(r);
}
static int nx_ui_touch(int x,int y,int count,int *selected,int *launch) {
    if(x>=95 && x<=785 && y>=210 && y<578) {
        int index=(*selected/8)*8+(y-210)/46;
        if(index>=0 && index<count) *selected=index;
        return 1;
    }
    if(x>=869 && x<=1182 && y>=215 && y<397) {
        int region=(y-215)/65;
        if(region>=0 && region<3) nx_region_setting=region;
        return 1;
    }
    if(x>=870 && x<=1182 && y>=440 && y<516) {*launch=1;return 1;}
    if(x>=870 && x<=1182 && y>=531 && y<586) {*launch=2;return 1;}
    return 0;
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
    nx_pad_init();
    SDL_SetMainReady();
    if(SDL_Init(SDL_INIT_VIDEO)!=0) {
        nx_error("Launcher video initialization failed");
        return 0;
    }
    SDL_Window *window=SDL_CreateWindow("Umbrella Mega Drive NX",
        SDL_WINDOWPOS_CENTERED,SDL_WINDOWPOS_CENTERED,1280,720,
        SDL_WINDOW_SHOWN|SDL_WINDOW_FULLSCREEN_DESKTOP);
    SDL_Renderer *renderer=window?SDL_CreateRenderer(window,-1,
        SDL_RENDERER_ACCELERATED|SDL_RENDERER_PRESENTVSYNC):NULL;
    if(!renderer && window) renderer=SDL_CreateRenderer(window,-1,SDL_RENDERER_SOFTWARE);
    if(!renderer) {
        if(window) SDL_DestroyWindow(window);
        SDL_Quit();
        nx_error("Launcher renderer unavailable");
        return 0;
    }
    SDL_RenderSetLogicalSize(renderer,1280,720);
    int launch=0;
    while(appletMainLoop()) {
        padUpdate(&pad);
        u64 b=padGetButtonsDown(&pad);
        if(b&HidNpadButton_Up) selected=(selected+count-1)%count;
        if(b&HidNpadButton_Down) selected=(selected+1)%count;
        if(b&(HidNpadButton_L|HidNpadButton_Left))
            nx_region_setting=(nx_region_setting+2)%3;
        if(b&(HidNpadButton_R|HidNpadButton_Right))
            nx_region_setting=(nx_region_setting+1)%3;
        if(b&HidNpadButton_B) break;
        if(b&HidNpadButton_X) launch=2;
        if(b&HidNpadButton_A) launch=1;
        if(b&HidNpadButton_Y) launch=3;
        SDL_Event ev;
        while(SDL_PollEvent(&ev)) {
            if(ev.type==SDL_QUIT) { launch=-1; break; }
            if(ev.type==SDL_FINGERDOWN) {
                nx_ui_touch((int)(ev.tfinger.x*1280),(int)(ev.tfinger.y*720),
                            count,&selected,&launch);
            }
            if(ev.type==SDL_MOUSEBUTTONDOWN) {
                nx_ui_touch(ev.button.x,ev.button.y,count,&selected,&launch);
            }
        }
        nx_ui_draw(renderer,count,selected);
        if(launch) {
            if(launch>0) {
                if(launch==2) *rom="builtin:diagnostic";
                else {
                    nx_video_bypass=(launch==3);
                    snprintf(chosen,sizeof(chosen),"%s%s",ROMS,names[selected]);
                    *rom=chosen;
                }
                ok=1;
            }
            break;
        }
        SDL_Delay(16);
    }
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
return ok;
}
int nx_pad_poll(void) {
    padUpdate(&pad);
    u64 held=padGetButtons(&pad);
    u64 down=padGetButtonsDown(&pad);
    if (down & HidNpadButton_ZR) nx_skip_request();
    if (down & HidNpadButton_L) nx_show_hud = !nx_show_hud;
    if (down & HidNpadButton_ZL) nx_light_probes = !nx_light_probes;
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
