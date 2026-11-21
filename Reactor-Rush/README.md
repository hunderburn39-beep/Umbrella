# Reactor Rush — V1.2

Slot de cascatas original em HTML/CSS/JavaScript, adaptada a telemóveis, jogada com **créditos virtuais**.

**Jogar online:** https://reactor-rush-umbrella.vercel.app/

## Novidades da V1.2

- Os símbolos premiados desaparecem antes da queda e os restantes **descem das suas posições anteriores**, coluna a coluna.
- Novos símbolos caem **a partir de cima da grelha**, com atraso ligeiramente diferente entre colunas.
- Fusão 2×2 reaparece quando a queda termina, para evitar sobreposições visuais.
- Movimento implementado com transformações GPU (CSS), com tempos ajustados ao Turbo e respeito pela opção de movimento reduzido.
- Melhoria leve na renderização do tabuleiro: sprites SVG reutilizados, sem filtros repetidos em cada símbolo.

## Mecânicas em desenvolvimento

- Grelha 7×7 e grupos de pelo menos cinco símbolos vizinhos.
- Cascatas com multiplicador até ×5.
- Fusão 2×2 de símbolos iguais com pagamento dobrado do grupo.
- Wilds, símbolos energizados e quatro transformações quânticas.
- Evento gigante a cada cinco transformações, jackpot progressivo virtual raro.
- Turbo, dez rodadas automáticas, som sintetizado, créditos virtuais gratuitos e recordes locais.

## Estrutura

O jogo está num único ficheiro [index.html](./index.html), sem dependências. A versão pública é publicada **manualmente** no Vercel, a partir do HTML deste repositório. Não há sincronização automática com GitHub.

## Validação

Testes em navegador Chromium simulado com tamanhos de 375×812, 390×844 e 428×926: verificação visual, queda animada, prémios e controlo automático. Mais 35 rodadas Turbo de resistência sem erros JS. Ainda não foi testado fisicamente no Safari do iPhone.

**Sem dinheiro real, depósitos ou levantamentos. Não tem RTP certificado nem reproduz código, arte, áudio ou matemática de outro jogo.**