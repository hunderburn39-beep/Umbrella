#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include "libretro.h"
extern bool sho_video_init(void);
extern void sho_video_close(void);
extern bool sho_video_format(enum retro_pixel_format);
extern void sho_video_refresh(const void *,unsigned,unsigned,size_t);
static PadState pad;
static bool environment(unsigned cmd,void *data){
    switch(cmd){
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:return sho_video_format(*(enum retro_pixel_format*)data);
    case RETRO_ENVIRONMENT_GET_CAN_DUPE:*(bool*)data=true;return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:*(bool*)data=false;return true;
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:*(const char**)data="sdmc:/switch/Super-Hang-On";return true;
    default:return false;
    }
}
static void audio(int16_t l,int16_t r){(void)l;(void)r;}
static size_t batch(const int16_t *s,size_t n){(void)s;return n;}
static void poll(void){padUpdate(&pad);}
static int16_t input(unsigned p,unsigned d,unsigned i,unsigned id){
    (void)i;if(p||d!=RETRO_DEVICE_JOYPAD)return 0;
    u64 k=0;
    switch(id){
    case RETRO_DEVICE_ID_JOYPAD_UP:k=HidNpadButton_Up;break;
    case RETRO_DEVICE_ID_JOYPAD_DOWN:k=HidNpadButton_Down;break;
    case RETRO_DEVICE_ID_JOYPAD_LEFT:k=HidNpadButton_Left;break;
    case RETRO_DEVICE_ID_JOYPAD_RIGHT:k=HidNpadButton_Right;break;
    case RETRO_DEVICE_ID_JOYPAD_B:k=HidNpadButton_B;break;
    case RETRO_DEVICE_ID_JOYPAD_A:k=HidNpadButton_A;break;
    case RETRO_DEVICE_ID_JOYPAD_Y:k=HidNpadButton_Y;break;
    case RETRO_DEVICE_ID_JOYPAD_START:k=HidNpadButton_Plus;break;
    }
    return !!(padGetButtons(&pad)&k);
}
int main(void){
    const char *path="sdmc:/switch/Super-Hang-On/game.bin";
    FILE *f=fopen(path,"rb");if(!f)return 1;
    if(fseek(f,0,SEEK_END)){fclose(f);return 1;}
    long n=ftell(f);rewind(f);
    if(n<=0||n>32*1024*1024){fclose(f);return 1;}
    void *rom=malloc((size_t)n);
    if(!rom||fread(rom,1,(size_t)n,f)!=(size_t)n){free(rom);fclose(f);return 1;}fclose(f);
    padConfigureInput(1,HidNpadStyleSet_NpadStandard);padInitializeDefault(&pad);
    if(!sho_video_init()){free(rom);return 1;}
    retro_set_environment(environment);
    retro_set_video_refresh(sho_video_refresh);
    retro_set_audio_sample(audio);retro_set_audio_sample_batch(batch);
    retro_set_input_poll(poll);retro_set_input_state(input);
    retro_init();
    struct retro_game_info game={.path=path,.data=rom,.size=(size_t)n,.meta=NULL};
    bool loaded=retro_load_game(&game);
    if(loaded){
        retro_set_controller_port_device(0,RETRO_DEVICE_JOYPAD);
        while(appletMainLoop()){
            padUpdate(&pad);
            if(padGetButtonsDown(&pad)&HidNpadButton_Minus)break;
            retro_run();
        }
        retro_unload_game();
    }
    retro_deinit();sho_video_close();free(rom);return loaded?0:1;
}
