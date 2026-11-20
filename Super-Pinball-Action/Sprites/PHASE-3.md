# Fase 3 — análise estática do vídeo (US)
ROM original do utilizador, não incluída neste repositório público.
- 0xCDB4: oito listas de fragmentos/âncoras; FFFF termina cada lista.
- 0xCDFC: 50 offsets de fragmentos; rotina C8D6–C974 escreve na RAM de fundo (70000 atributos, 74000 números). 0x80 OR do byte alto do ID; 0x81 desloca a âncora; FF termina. 253 colocações de células. As imagens reconstruídas mostram olhos, bocas e outros fragmentos de animações faciais.
- 0xD2FE–0xD3AB: 87 entradas de pares de sprites de 16×16; base 0x2000 OR (word & 0xfff); grupo de cor no nibble alto. A segunda peça usa base+4, x+16. Rotina CA50–CA9C.
- 0xD190: quatro pares de offsets de listas e contadores de espera; 0xCAA4: 35 pares y/x. 0x80 apaga/desativa 70 entradas de sprite RAM; FF termina. 153 eventos, incluindo um clear. Contadores brutos, não milissegundos.
- 16 blocos candidatos a flippers (64×64) nos intervalos 0200–03FF e 0800–09FF e 64 sub-blocos de 32×32. Identificação visual, não frames confirmados.
- Paletas estáticas não equivalem à seleção de paletas executada pelo hardware. Ainda não são mesas completas nem jogo funcional.
## Reproduzir tabelas
Após executar extract.py na ROM local: python Sprites/trace_tables.py extracted/cpu/us/m68000.bin trace.json
Referência de layout: MAME src/mame/tecmo/spbactn.cpp, src/mame/shared/tecmo_spr.cpp (BSD-3-Clause).
