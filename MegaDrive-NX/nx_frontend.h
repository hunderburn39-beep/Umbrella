#pragma once
int nx_choose_rom(char **rom);
void nx_error(const char *message);
void nx_pad_init(void);
int nx_pad_poll(void);
int nx_video_init(int ntsc);
