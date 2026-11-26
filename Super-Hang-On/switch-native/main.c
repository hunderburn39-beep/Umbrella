#include <switch.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include "libretro.h"
#ifdef SHO_EMBED_ROM
extern const unsigned char sho_rom_start[],sho_rom_end[];
#endif
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
extern bool sho_audio_init(double);
extern void sho_audio_sample(int16_t,int16_t);
extern size_t sho_audio_batch(const int16_t *,size_t);
extern void sho_audio_close(void);
static u64 held;
static HidAnalogStickState stick;
static void poll(void){
    padUpdate(&pad);
    held=padGetButtons(&pad);
    stick=padGetStickPos(&pad,0);
}
static int16_t input(unsigned p,unsigned d,unsigned i,unsigned id){
    (void)i;
    if(p||d!=RETRO_DEVICE_JOYPAD)return 0;
    switch(id){
    case RETRO_DEVICE_ID_JOYPAD_UP:return !!(held&HidNpadButton_Up)||stick.y>8192;
    case RETRO_DEVICE_ID_JOYPAD_DOWN:return !!(held&HidNpadButton_Down)||stick.y< -8192;
    case RETRO_DEVICE_ID_JOYPAD_LEFT:return !!(held&HidNpadButton_Left)||stick.x< -8192;
    case RETRO_DEVICE_ID_JOYPAD_RIGHT:return !!(held&HidNpadButton_Right)||stick.x>8192;
    /* Genesis Plus GX maps RetroPad Y/B/A to Mega Drive A/B/C. */
    case RETRO_DEVICE_ID_JOYPAD_Y:return !!(held&(HidNpadButton_Y|HidNpadButton_ZL));
    case RETRO_DEVICE_ID_JOYPAD_B:return !!(held&(HidNpadButton_B|HidNpadButton_ZR));
    case RETRO_DEVICE_ID_JOYPAD_A:return !!(held&(HidNpadButton_A|HidNpadButton_R));
    case RETRO_DEVICE_ID_JOYPAD_START:return !!(held&HidNpadButton_Plus);
    case RETRO_DEVICE_ID_JOYPAD_X:return !!(held&HidNpadButton_X);
    case RETRO_DEVICE_ID_JOYPAD_L:return !!(held&HidNpadButton_L);
    case RETRO_DEVICE_ID_JOYPAD_R:return !!(held&HidNpadButton_R);
    case RETRO_DEVICE_ID_JOYPAD_SELECT:return !!(held&HidNpadButton_Minus);
    default:return 0;
    }
}
int main(void){
    const char *path="sdmc:/switch/Super-Hang-On/game.bin";
#ifdef SHO_EMBED_ROM
    long n=(long)((uintptr_t)sho_rom_end-(uintptr_t)sho_rom_start);
    if(n!=524288)return 1;
    void *rom=malloc((size_t)n);
    if(!rom)return 1;
    __builtin_memcpy(rom,sho_rom_start,(size_t)n);
#else
    FILE *f=fopen(path,"rb");if(!f)return 1;
    if(fseek(f,0,SEEK_END)){fclose(f);return 1;}
    long n=ftell(f);rewind(f);
    if(n<=0||n>32*1024*1024){fclose(f);return 1;}
    void *rom=malloc((size_t)n);
    if(!rom||fread(rom,1,(size_t)n,f)!=(size_t)n){free(rom);fclose(f);return 1;}fclose(f);
#endif
    padConfigureInput(1,HidNpadStyleSet_NpadStandard);padInitializeDefault(&pad);
    if(!sho_video_init()){free(rom);return 1;}
    retro_set_environment(environment);
    retro_set_video_refresh(sho_video_refresh);
    retro_set_audio_sample(sho_audio_sample);retro_set_audio_sample_batch(sho_audio_batch);
    retro_set_input_poll(poll);retro_set_input_state(input);
    retro_init();
    struct retro_game_info game={.path=path,.data=rom,.size=(size_t)n,.meta=NULL};
    bool loaded=retro_load_game(&game);
    if(loaded){
        struct retro_system_av_info av;
        retro_get_system_av_info(&av);
        sho_audio_init(av.timing.sample_rate);
        retro_set_controller_port_device(0,RETRO_DEVICE_JOYPAD);
        while(appletMainLoop()){
            padUpdate(&pad);
            if((padGetButtons(&pad)&(HidNpadButton_Plus|HidNpadButton_Minus))==(HidNpadButton_Plus|HidNpadButton_Minus))break;
            retro_run();
        }
        sho_audio_close();
        retro_unload_game();
    }
    retro_deinit();sho_video_close();free(rom);return loaded?0:1;
}
