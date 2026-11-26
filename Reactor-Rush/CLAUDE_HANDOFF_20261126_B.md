# Claude → ChatGPT — 2026-11-26 (sessão 3): opção B implementada

Decisão OWNER_DECISION_OPTION_B reconhecida e feita. Em `main`: merge `cb7f2320` (commit de trabalho `4c57f9fb`).

## Feito
- `engine/engine.js` é o único motor; novo `playRoundTrace` (mesmo RNG que `playRound`; baseline de 200 000 rondas idêntico).
- `index.html` só anima fotogramas do motor. Motor alternativo arquivado em `archive/rr-engine-alt/` (sem uso).
- Testes: `node --test tests/engine.test.js tests/trace.test.js` = 22/22; `python3 tests/ui-tests.py` = 37/37 (Chrome headless; inclui repetição determinística de 12 sementes na página).
- RTP verificado de forma independente: 4 000 000 rondas, semente 20261127: 95,997 % (IC 95 % 95,56–96,44 %). Ficheiro: `sim/results-verify-seed20261127-4M.json`.
- Detalhes: `REPORT-V5.0.md` e `DEVELOPMENT_LOG.md` (Session 3).

## Por fazer / NÃO verificado
1. Confirmar se o GitHub Pages publicou (o ambiente do Claude não alcança github.io): https://hunderburn39-beep.github.io/Umbrella/Reactor-Rush/ e separador Actions. Deve mostrar "V5.0 • FREE PLAY".
2. Safari e iPhone reais (layout 16:9/9:16, áudio iOS, zoom/gestos). Nada disto foi testado.
3. Ouvir o áudio (reatores, queda, big win) e confirmar que a música Quantum Arcade não é interrompida.
4. PDF oficial (403): a tabela de prémios é original e provisória, está assim marcada no menu.
5. Volatilidade muito abaixo da referência (máx. 268× vs 5083×): os patamares QUANTUM WIN/MAX WIN quase não aparecem.
6. Correr os testes com `node --test tests/engine.test.js tests/trace.test.js`; `node --test tests` apanha ficheiros que não são testes.

Antes de editar: `git fetch` e ler o log.
