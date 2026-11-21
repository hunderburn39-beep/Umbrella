# Reactor Rush — V1.3

**[🎰 Jogar a versão pública](https://reactor-rush-umbrella.vercel.app/)**

Slot original de cascatas em HTML5/CSS/JavaScript, com visual vertical otimizado para iPhone. Funciona com **créditos fictícios**, sem depósitos, levantamentos nem prémios em dinheiro real. Esta é uma criação independente; não usa arte, código, áudio ou matemática original da Play’n GO e não tem RTP certificado.

## Como jogar
- Grelha 7×7, sem linhas; 5+ criaturas iguais adjacentes vencem.
- Wild substitui uma cor. **Cada casa, incluindo Wild, pode ser contabilizada uma única vez por cascata**, sem pagamentos duplicados.
- Grupo com bloco 2×2 ganha criatura visual gigante e duplicação do pagamento desse grupo.
- Vitórias geram novas quedas, com multiplicador por cascata até ×5.
- Energia quântica ativa efeitos; de cinco em cinco ativações ocorre um evento gigante.
- Jackpot virtual acumulado ao longo das rodadas, com sorteio raro em eventos gigantes.
- Turbo, 10 rodadas automáticas, crédito grátis de +1.000 CR e gravação local do saldo e recordes.

## Alterações da V1.3
- **49 casas persistentes**: deixam de ser destruídas/recriadas a cada queda; apenas as referências dos SVG mudam.
- **Wild sem dupla contagem**: atribuição por grupo de prémio, recalculando grupos após reservar as casas.
- **Pop-up flutuante de prémio** durante cascatas e pequeno realce do saldo.
- Afinamentos de ecrãs estreitos e respeito pela preferência de movimento reduzido.

## Verificações
- Jogabilidade testada em 375×812, 390×844 e 428×926 (motor Chromium).
- Teste automático de 1.500 grelhas aleatórias e 20 rodadas Turbo, sem falhas de execução.
- Botões, Auto ×10 e permanência dos 49 nós da grelha confirmados.
- **Safari num iPhone físico ainda não verificado.**

## Publicação
Código-fonte: `index.html` — jogo autocontido e sem bibliotecas externas. O GitHub armazena a fonte em `Umbrella/Reactor-Rush`. O Vercel é publicado manualmente com este mesmo HTML; não há sincronização automática ao fazer push.
