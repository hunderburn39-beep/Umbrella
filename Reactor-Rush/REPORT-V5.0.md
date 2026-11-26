# Reactor Rush V5.0 — Relatório técnico

Modo Free Play, créditos exclusivamente virtuais. Referência: Reactoonz 2 (Play'n GO).

## 1. Limitações e o que NÃO está confirmado (ler primeiro)

* **O regulamento oficial do PokerStars não foi lido.** O PDF indicado não pôde ser obtido neste ambiente. As regras e a tabela de prémios foram reconstruídas a partir de fontes secundárias (casinorange.com, allslotsonline.casino, páginas de revisão), concordantes entre si, mas **não são o documento oficial**. Devem ser confrontadas com o PDF antes de se afirmar fidelidade.
* **A matemática não é a do jogo original.** Pesos dos símbolos, probabilidade de Wilds não carregados e mecânica detalhada do Fluctometer, Wild Pair Explosion e prioridades de execução são **interpretação própria**, calibrada para aproximar o RTP alvo.
* **RTP observado: 97,47%** (IC 95%: 96,37%–98,57%) em 20 000 000 de rondas. O alvo 96,20% **não foi demonstrado**: fica fora do intervalo. O RTP teórico oficial do Reactoonz 2 (96,20%) é só um alvo de calibração. Desvio-padrão por ronda ≈ 25,1× a aposta; para um IC de ±0,2% seriam precisas centenas de milhões de rondas.
* **Safari/iPhone não foram testados.** Só Chrome headless (Playwright, Linux). Compatibilidade de áudio com Safari iOS segue boas práticas (AudioContext iniciado em gesto do utilizador) mas **não está verificada**. O áudio não foi ouvido; os sons só foram validados quanto a ausência de erros.
* Patamares de celebração (BIG 10×, MEGA 20×, SUPER 50×, EPIC 100×, QUANTUM 250×, MAX 1000×) são **escolha própria**; não há patamares oficiais documentados.
* Limiares do Quantumeter (55/85/110/135) e Fluctometer (11 símbolos, 1–3 Wilds): de fontes secundárias; não verificados no regulamento.

## 2. Alterações

* Novo `rr-engine.js`: motor puro (sem DOM/áudio), grelha 7×7, 8 símbolos, grupos ortogonais ≥5, cascatas, Wilds, reatores, PRNG com semente (mulberry32).
* Novo `rr-sim.js`: simulador independente e reproduzível (`node rr-sim.js rondas semente saída.json`).
* `index.html`: lógica antiga substituída por reprodução das rondas do motor; removidos mecanismos antigos incompatíveis (Quantum Leap, fila de funcionalidades, jackpot); novos painéis Quantumeter/Fluctometer em horizontal e vertical; mensagens 3D sem caixas (11); menu de informações com tabela de prémios e explicação das funcionalidades; botões circulares corrigidos para lado = altura.
* Preservados: música `Quantum Arcade.mp3`, imagens de fundo e CSS de skins aprovados.
* Backup: `Reactor-Rush/backup-V4.0/`.

## 3. Funcionalidades implementadas

Quantumeter (4 níveis), Fluctometer, Electric Wilds, Wilds não carregados, Wild Pair Explosion, Energoon 1×1 (×4), Energoon 2×2, Gargantoon 3×3 com divisão 3×3 → dois 2×2 → nove 1×1, Sobrecarga ×2. Animação/som individual por reator e relâmpagos entre Wilds.

## 4. Testes

* `node tests/engine-tests.js`: **22/22** (tabela completa 8 símbolos × tamanhos 5–49; mapeamento de escalões; deteção de grupos contra oráculo independente em 30 000 tabuleiros; Wilds; reatores 1–4 individuais e simultâneos; Gargantoon e divisões; multiplicador ×2; Fluctometer; Wild Pair Explosion; cascatas; reprodutibilidade; ausência de jackpot). Resultados em `tests/results-engine.json`.
* `python3 tests/ui-tests.py`: **25/25** em Chrome headless (49 células; grelha quadrada em horizontal, vertical e 16:9; botões circulares; 11 mensagens sem caixa; patamares; menu; 60 rondas em turbo sem erros JavaScript; saldo; long task < 400 ms; demo do Gargantoon sem alterar saldo). Resultados em `tests/results-ui.json`.
* **Não testado:** Safari, iPhone real, qualidade/mistura do áudio ao ouvido, gestos de zoom em ecrã tátil, ativação de todos os cenários em jogo real (cobertos por testes do motor, não por rondas na interface).

## 5. Simulação

| Execução | Rondas | Semente | RTP |
|---|---|---|---|
| 1 | 5 000 000 | 101 | 96,23% |
| 2 | 5 000 000 | 202 | 98,14% |
| 3 | 5 000 000 | 303 | 96,18% |
| 4 | 5 000 000 | 404 | 99,35% |
| **Total** | **20 000 000** | | **97,47% (96,37–98,57)** |

Execução de 1 000 000 (semente 20260101): 99,29% (94,32–104,25). Frequência de prémio: 44,77%. Maior prémio observado: 2972×. Rondas com Electric Wild 16,2%; Energoon 1×1 0,53%; Energoon 2×2 0,34%; Gargantoon 0,27%; Sobrecarga ×2 0,27%; Wild Pair Explosion 0,95%; Fluctometer cheio 1,2%. Distribuição completa em `sim/pooled-20M.json`.

A calibração de pesos foi feita com as mesmas sementes de simulação, por isso há risco de sobreajuste; as execuções finais usaram sementes diferentes das de calibração.

## 6. Pendências

Validar regras contra o PDF oficial; testar em Safari/iPhone; ouvir e afinar o áudio; recalibrar para aproximar 96,20% com um IC mais estreito.
