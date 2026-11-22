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
unsigned long long nx_get_worker_clock(void);
void nx_video_show_boot(unsigned long long clocks);
void nx_diag_capture(unsigned long long reads,unsigned long long writes,int display,int reset);
void nx_diag_read(unsigned long long *reads,unsigned long long *writes,int *display,int *reset);
void nx_bus_publish(unsigned int address,unsigned long long direct_writes);
void nx_bus_read(unsigned int *address,unsigned long long *direct_writes);
