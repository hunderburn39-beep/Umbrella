.section .rodata.sho_rom,"a",%progbits
.balign 16
.global sho_rom_start, sho_rom_end
sho_rom_start:
.incbin "game.bin"
sho_rom_end:
