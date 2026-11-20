# Fase 7 — Cinemática
- Correção: B18–B1D é SUB.L #$10001010. Não se substitui o byte baixo pelo estado. Indexação validada em 114688 píxeis.
- 2C52 inicializa A1=40138, A2=40140, A3=40178. 5A2–5D6 guarda módulos de seis velocidades e máscara de sinais, soma ASR.L #3 aos seis componentes da posição. 62A–62E repete oito vezes. O código traduz a integração isolada, sem as rotinas intercaladas.
- 7DA carrega 0x3317; estado 0 soma-o ao primeiro componente (mesa 2 usa tabela auxiliar). 806–80C: 25 offsets com base 80E.
- 8B6–8C4: palavras altas da posição 11F4/102C. AAE–AC2: 256 bytes em FC0–10BF, negação e extensão do byte para a palavra alta da velocidade, soma 0x3317. Caminho 954 utiliza índice 226 (26).
- Testes locais: 114688 índices, 12000 operações com BigInt, 2000 traços de oito subpassos, 768 lançamentos, 4480 respostas. Interface de inspeção testada em Chromium. Não houve validação contra uma execução original. Restantes estados, colisões, áudio e multibola por ligar.
- Executar: python decode_kinematics.py caminho/m68000.bin kinematics.json. Não é emulador; requer ROM local e decoder da fase anterior.
