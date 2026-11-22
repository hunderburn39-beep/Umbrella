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
extern int nx_region_setting;
extern int nx_show_hud;
extern int nx_light_probes;
void nx_cpu_boost_start(void);
void nx_cpu_boost_stop(void);
void nx_cpu_boost_info(unsigned int *hz,int *status);
void nx_flush_worker_stage(int force);
void nx_disable_runtime_io(void);
unsigned long long nx_get_worker_clock(void);
void nx_video_show_boot(unsigned long long clocks);
int nx_video_has_picture(void);
void nx_diag_capture(unsigned long long reads,unsigned long long writes,int display,int reset);
void nx_diag_read(unsigned long long *reads,unsigned long long *writes,int *display,int *reset);
void nx_bus_publish(unsigned int address,unsigned long long direct_writes);
void nx_bus_read(unsigned int *address,unsigned long long *direct_writes);
void nx_ack_publish(unsigned long long ack,unsigned long long changes,unsigned int flags);
void nx_ack_read(unsigned long long *ack,unsigned long long *changes,unsigned int *flags);
void nx_handshake_publish(unsigned long long sel,unsigned long long strobe,unsigned long long ready);
void nx_handshake_read(unsigned long long *sel,unsigned long long *strobe,unsigned long long *ready);
void nx_vdp_state_publish(unsigned long long edges,unsigned int data,unsigned int mode);
void nx_vdp_state_read(unsigned long long *edges,unsigned int *data,unsigned int *mode);
void nx_decode_publish(unsigned long long decode,unsigned long long gate,unsigned long long ctrl);
void nx_decode_read(unsigned long long *decode,unsigned long long *gate,unsigned long long *ctrl);
void nx_drive_publish(unsigned long long clocks,unsigned int word);
void nx_drive_read(unsigned long long *clocks,unsigned int *word);
void nx_pipe_publish(unsigned long long cmd,unsigned long long gate,unsigned long long req);
void nx_pipe_read(unsigned long long *cmd,unsigned long long *gate,unsigned long long *req);
/* Experimental ZR: acknowledge one stuck VDP write, without patching the ROM. */
void nx_skip_request(void);
int nx_skip_take(void);
void nx_skip_report(int status);
void nx_skip_read(unsigned int *tries,int *status);

unsigned long long nx_prof_begin(void);
void nx_prof_end(int id,unsigned long long start);
unsigned int nx_prof_avg_ns(int id);

void nx_trace_push(unsigned int addr,unsigned int data,unsigned int flags);
void nx_trace_read(unsigned int back,unsigned int *addr,unsigned int *data,unsigned int *flags);
