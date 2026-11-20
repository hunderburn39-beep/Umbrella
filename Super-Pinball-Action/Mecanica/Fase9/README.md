# Fase 9 — colisões
- 0x2C76 inicializa $40304 com $4AAB2CCD (passos de subida 19115 e descida 11469). O visor local usa oito subpassos e cadência estimada do hardware. Alterações em execução ainda não investigadas.
- 0x400–42E multiplicação unsigned 32x32, parte alta. 0x6BC–7AA troca contribuições de velocidade entre duas bolas. Tradução de contacto isolado; não inclui persistência de flags e todos os pares do ciclo de três bolas.
- 0x82F6–83FA seleção de candidatos por dificuldade, mesa, caminho e posição. Base 0x1804A, 32 grelhas lógicas de 896 posições, 1.204 listas (incluindo repetições), 4.720 referências e 727 registos distintos de 16 bytes. Seletor negativo usa tabela 0x1F1C8 e frame do flipper. Handlers geométricos a partir de 0x840E ainda não portados.
- 0x10C0–113C: descriptor da bola nos subpassos 4 e 0, tiles 0x50, 0x60, 0x70, 0x80. Renderização dinâmica por integrar.
- Testes locais: 20.000 multiplicações, 16.800 transferências contra referência BigInt, 28.672 células e 200.704 consultas de frame. Chromium verificou 32 combinações e comandos. Não houve comparação dinâmica com o jogo original; não é versão jogável.
- Executar python decode9.py spbactn.zip data.json. collision.js depende de Fase8/flippers.js. ROM e imagens não publicadas.
