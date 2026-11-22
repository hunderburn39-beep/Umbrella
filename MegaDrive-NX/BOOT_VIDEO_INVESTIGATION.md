# MegaDrive-NX: diagnóstico de arranque sem vídeo

## Referências técnicas verificadas (2026-11-22)
- Nuked-MD: https://github.com/nukeykt/Nuked-MD
- Nuked-MD-FPGA: https://github.com/nukeykt/Nuked-MD-FPGA
- Genesis Plus GX, cartucho: https://github.com/ekeeke/Genesis-Plus-GX/blob/master/core/cart_hw/md_cart.c
- Genesis Plus GX, controlo VDP: https://github.com/ekeeke/Genesis-Plus-GX/blob/master/core/vdp_ctrl.c

## Observações no hardware
- Super Hang-On fica sem imagem na Switch, quer o lançamento seja por A, quer por Y.
- Contadores anteriores: FRAMES=1, PIXELS=0; CPU/BOARD/CHIP ~12 milhões, SEL/STB/RDY=0.
- CHIP e SEL mediam a mesma seleção mas davam valores contraditórios; os contadores foram unificados. Falta repetir o teste na Switch.
- Não assumir que o contador CPU significa instruções executadas: pode ser apenas amostragem de um barramento parado.

## Hipóteses por ordem de prioridade
1. O 68000 não completa a sequência de reset e as leituras dos vetores de ROM.
2. O cartucho é carregado, mas o barramento não entrega palavras válidas ao 68000 durante os ciclos de leitura.
3. O 68000 corre, mas o FC1004/VDP não descodifica as escritas em $C00000/$C00004.
4. O VDP gera relógio mas a extração dos píxeis ou SDL não apresenta a imagem.
5. Desempenho insuficiente. Só avaliar depois de demonstrar progressão funcional.

## Teste decisivo a implementar
Capturar os primeiros 32 acessos de leitura do 68000 após reset:
- ciclo mestre, endereço de palavra e endereço em bytes;
- AS, RW, UDS, LDS, DTACK, RESET, HALT;
- CE0, CAS0, valor de md.vdata e valor entregue a m68k.input.i_data;
- distinguir amostras repetidas do mesmo acesso de transações novas.
A primeira leitura de reset deve obter o stack pointer inicial em $000000 e a segunda o program counter em $000004, com a granularidade adequada às palavras de 16 bits. Validar contra os primeiros 8 bytes da ROM carregada. Não inferir execução a partir de ciclos de relógio.

## Critérios de aceitação
A. ROM reconhecida, tamanho e vetores iniciais válidos.
B. Quatro palavras dos vetores iniciais observadas no barramento com os mesmos valores da ROM.
C. PC de arranque não nulo e transações de instruções distintas.
D. Primeira escrita VDP observada com seleção e strobes coerentes.
E. PIXELS > 0 e FRAMES a avançar no modo normal.
F. Só depois otimizar frequência/CPU e áudio.

## Nota
A comparação com Genesis Plus GX serve como oráculo de comportamento, não para substituir a simulação de chips Nuked-MD. Os testes estáticos existentes verificam código e não demonstram que os sinais estejam temporalmente corretos.
