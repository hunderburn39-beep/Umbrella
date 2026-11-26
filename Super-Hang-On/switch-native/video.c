#include <switch.h>
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include "libretro.h"

/* Native libnx framebuffer; nearest-neighbour full viewport and subtle
 * output-pixel RGB phosphor mask. No scanlines, blur or curvature. */
static Framebuffer fb;
static bool ready;
static enum retro_pixel_format fmt = RETRO_PIXEL_FORMAT_0RGB1555;
static uint32_t *last;
static unsigned sw,sh;
static uint32_t lut[3][65536];
static unsigned cached_fmt=999;
static uint16_t *xmap,*ymap;
static unsigned mapw,maph;
static uint32_t mask(unsigned r,unsigned g,unsigned b,unsigned phase){
    if(phase!=0) r=r*15/16;
    if(phase!=1) g=g*15/16;
    if(phase!=2) b=b*15/16;
    return (uint32_t)r | ((uint32_t)g<<8) | ((uint32_t)b<<16) | 0xff000000u;
}
static void make_lut(void){
    if(cached_fmt==(unsigned)fmt)return;
    for(unsigned i=0;i<65536;i++){
        unsigned r,g,b;
        if(fmt==RETRO_PIXEL_FORMAT_RGB565){
            r=((i>>11)&31)*255/31;g=((i>>5)&63)*255/63;b=(i&31)*255/31;
        }else{
            r=((i>>10)&31)*255/31;g=((i>>5)&31)*255/31;b=(i&31)*255/31;
        }
        for(unsigned p=0;p<3;p++)lut[p][i]=mask(r,g,b,p);
    }
    cached_fmt=fmt;
}
bool sho_video_format(enum retro_pixel_format f){
    if(f!=RETRO_PIXEL_FORMAT_RGB565 && f!=RETRO_PIXEL_FORMAT_0RGB1555 && f!=RETRO_PIXEL_FORMAT_XRGB8888)return false;
    fmt=f;return true;
}
bool sho_video_init(void){
    if(R_FAILED(framebufferCreate(&fb,nwindowGetDefault(),1280,720,PIXEL_FORMAT_RGBA_8888,2)))return false;
    if(R_FAILED(framebufferMakeLinear(&fb))){framebufferClose(&fb);return false;}
    xmap=malloc(1280*sizeof(*xmap));ymap=malloc(720*sizeof(*ymap));
    if(!xmap||!ymap){free(xmap);free(ymap);framebufferClose(&fb);return false;}
    ready=true;return true;
}
void sho_video_close(void){
    if(ready)framebufferClose(&fb);
    free(last);free(xmap);free(ymap);last=NULL;ready=false;
}
void sho_video_refresh(const void *data,unsigned w,unsigned h,size_t pitch){
    if(!ready||!w||!h||w>2048||h>2048)return;
    if(!data){return;} /* framebuffer retains previous presented frame */
    unsigned bytes=fmt==RETRO_PIXEL_FORMAT_XRGB8888?4:2;
    if(pitch<(size_t)w*bytes)return;
    if(mapw!=w||maph!=h){
        for(unsigned x=0;x<1280;x++)xmap[x]=(uint16_t)((uint64_t)x*w/1280);
        for(unsigned y=0;y<720;y++)ymap[y]=(uint16_t)((uint64_t)y*h/720);
        mapw=w;maph=h;
    }
    if(bytes==2)make_lut();
    u32 stride=0;uint8_t *dst=framebufferBegin(&fb,&stride);
    if(!dst)return;
    for(unsigned y=0;y<720;y++){
        const uint8_t *src=(const uint8_t*)data+(size_t)ymap[y]*pitch;
        uint32_t *row=(uint32_t*)(dst+(size_t)y*stride);
        for(unsigned x=0;x<1280;x++){
            unsigned p=x%3;
            if(bytes==2){uint16_t v;memcpy(&v,src+2*xmap[x],2);row[x]=lut[p][v];}
            else{uint32_t v;memcpy(&v,src+4*xmap[x],4);row[x]=mask((v>>16)&255,(v>>8)&255,v&255,p);}
        }
    }
    framebufferEnd(&fb);
}
