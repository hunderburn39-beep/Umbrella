#include <switch.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdlib.h>
#include <malloc.h>
#include <string.h>

#define COUNT 3
#define FRAMES 1024
#define BYTES (FRAMES*2*sizeof(int16_t))
static AudioOutBuffer buffers[COUNT];
static bool busy[COUNT],ready;
static unsigned used;
static int current=-1;
static double rate=48000.0,phase;
static void reclaim(void){
    AudioOutBuffer *released=NULL;u32 count=0;
    if(R_SUCCEEDED(audoutGetReleasedAudioOutBuffer(&released,&count))){
        for(unsigned i=0;i<COUNT;i++){
            bool in_use=true;
            if(busy[i]&&R_SUCCEEDED(audoutContainsAudioOutBuffer(&buffers[i],&in_use))&&!in_use)busy[i]=false;
        }
    }
}
bool sho_audio_init(double source_rate){
    if(source_rate<8000.0||source_rate>192000.0)return false;
    if(R_FAILED(audoutInitialize()))return false;
    if(audoutGetSampleRate()!=48000||audoutGetChannelCount()!=2){audoutExit();return false;}
    memset(buffers,0,sizeof(buffers));memset(busy,0,sizeof(busy));
    for(unsigned i=0;i<COUNT;i++){
        buffers[i].buffer=memalign(0x1000,BYTES);
        if(!buffers[i].buffer){
            for(unsigned j=0;j<i;j++)free(buffers[j].buffer);
            audoutExit();return false;
        }
        buffers[i].buffer_size=BYTES;buffers[i].data_size=BYTES;
    }
    if(R_FAILED(audoutStartAudioOut())){
        audoutExit();for(unsigned i=0;i<COUNT;i++)free(buffers[i].buffer);return false;
    }
    rate=source_rate;phase=0;used=0;current=-1;ready=true;return true;
}
static int acquire(void){
    reclaim();
    for(unsigned i=0;i<COUNT;i++)if(!busy[i])return (int)i;
    AudioOutBuffer *released=NULL;u32 count=0;
    audoutWaitPlayFinish(&released,&count,20000000ULL);
    reclaim();
    for(unsigned i=0;i<COUNT;i++)if(!busy[i])return (int)i;
    return -1;
}
static void emit(int16_t l,int16_t r){
    if(current<0){current=acquire();if(current<0)return;used=0;}
    int16_t *dst=buffers[current].buffer;
    dst[used*2]=l;dst[used*2+1]=r;
    if(++used==FRAMES){
        if(R_SUCCEEDED(audoutAppendAudioOutBuffer(&buffers[current])))busy[current]=true;
        current=-1;used=0;
    }
}
void sho_audio_sample(int16_t l,int16_t r){
    if(!ready)return;
    phase+=48000.0;
    while(phase>=rate){emit(l,r);phase-=rate;}
}
size_t sho_audio_batch(const int16_t *s,size_t n){
    if(!s)return 0;
    for(size_t i=0;i<n;i++)sho_audio_sample(s[i*2],s[i*2+1]);
    return n;
}
void sho_audio_close(void){
    if(!ready)return;
    ready=false;audoutStopAudioOut();audoutExit();
    for(unsigned i=0;i<COUNT;i++)free(buffers[i].buffer);
    current=-1;used=0;
}
