#pragma once
int nx_choose_rom(char **rom);
void nx_error(const char *message);
void nx_pad_init(void);
int nx_pad_poll(void);
int nx_video_init(int ntsc);
void nx_stage(const char *step);
void nx_worker_stage(const char *step);
void nx_worker_progress(unsigned long long clock, const char *phase);
extern int nx_video_bypass;
void nx_flush_worker_stage(int force);
void nx_disable_runtime_io(void);
