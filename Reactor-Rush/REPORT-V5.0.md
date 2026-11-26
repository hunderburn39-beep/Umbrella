# Reactor Rush V5.0 — Relatório técnico (opção B: motor único `engine/engine.js`)

Modo Free Play, créditos exclusivamente virtuais. Referência: Reactoonz 2 (Play'n GO).

## 1. Limitações (ler primeiro)
* **O regulamento oficial do PokerStars não foi lido** (HTTP 403 em todas as sessões). A **tabela de prémios é original e provisória deste projeto**, não a oficial. Limiares do Quantumeter (55/85/110/135) vêm de fontes secundárias; muitas regras de pormenor são interpretação própria (ver `engine/ASSUMPTIONS.md`).
* **A matemática não é a do original.** O RTP observado só diz respeito a este jogo.
* **Volatilidade muito menor que a referência:** maior prémio observado ≈ 270× (4M rondas) contra um máximo declarado de 5083×. Os patamares MAX WIN (1000×) e QUANTUM WIN (250×) quase nunca aparecem em jogo real.
* **Safari e iPhone não foram testados.** Só Chrome headless (Linux). O áudio não foi ouvido (só validado quanto a erros).
* Patamares das mensagens BIG/MEGA/SUPER/EPIC/QUANTUM/MAX (10/20/50/100/250/1000×) são escolha própria.

## 2. Arquitetura
* `engine/engine.js` — único motor (sem DOM/áudio), PRNG com semente. Novo: `playRoundTrace(rng,cfg)` devolve a mesma ronda que `playRound` (mesmo consumo do RNG) mais uma lista de fotogramas (`start`, `win`, `level`, `explosion`, `settle`).
* `index.html` — apenas anima os fotogramas; não contém lógica de jogo. Mensagens 3D sem caixas, tabela de prémios, painéis Quantumeter/Fluctometer (horizontal e vertical), botões circulares corrigidos.
* `sim/run-sim.js` — simulador reproduzível (inalterado). `archive/rr-engine-alt/` — o motor alternativo da sessão 2, arquivado, sem uso.
* Preservados: `Quantum Arcade.mp3`, imagens e CSS aprovados. Backup V4.0 em `backup-V4.0/`.

## 3. Testes
* `node --test tests/engine.test.js tests/trace.test.js`: **22/22** (16 da sessão 1 + 6 novos: o modo de registo não altera a ronda em 20 000 rondas e mantém o RNG sincronizado; repetição determinística; fotogramas bem formados e soma dos ganhos = total; os 4 níveis de reator; Gargantoon 9/4 células; ×2 só com peça de Gargantoon).
* `python3 tests/ui-tests.py`: **37/37** em Chrome headless — 49 células; grelha quadrada em horizontal, vertical e 16:9; botões circulares; 11 mensagens sem caixa; patamares; menu com tabela; **repetição determinística na interface** (12 sementes, incluindo explosões e os 4 reatores: saldo final = resultado do motor, tolerância 0,01 por arredondamentos por cascata); 60 rondas sem erros JavaScript; long task < 400 ms; demo Gargantoon sem alterar saldo.
* **Não testado:** Safari, iPhone real, áudio ao ouvido, zoom/gestos em ecrã tátil, GitHub Pages (o ambiente do Claude não alcança github.io).

## 4. RTP e simulação (motor `engine/engine.js`)
| Execução | Rondas | Semente | RTP | IC 95% |
|---|---|---|---|---|
| Sessão 1 | 2 000 000 | 424242 | 95,84% | 95,22–96,46% |
| Sessão 1 | 2 000 000 | 90210 | 95,64% | 95,02–96,26% |
| **Verificação independente (esta sessão)** | **4 000 000** | **20261127** | **95,997%** | **95,56–96,44%** |

Frequência de prémio 48,9%; Gargantoon em ≈0,98% das rondas; explosões 0,15/ronda; maior prémio 268×. O IC é uma aproximação normal; os prémios têm cauda pesada, por isso pode ser otimista. `payScale` (1,2258) foi calibrado na semente 111; as validações usaram sementes diferentes. O RTP de referência 96,20% está dentro dos intervalos, mas isto não prova nada sobre o jogo original.

## 5. Pendências
Safari/iPhone; ouvir o áudio; PDF oficial (tabela real e volatilidade); verificar o URL do Pages.
