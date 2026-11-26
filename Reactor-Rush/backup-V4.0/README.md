# Reactor Rush — V2.0

**[Jogar Reactor Rush](https://reactor-rush-umbrella.vercel.app/?v=1.9)**

Jogo original de cascatas com créditos exclusivamente virtuais. Sem depósitos, levantamentos ou prémios em dinheiro real.

## V1.7 — horizontal
- Utiliza a arte horizontal aprovada como moldura e fundo, com criaturas 3D recortadas da mesma imagem.
- Tabuleiro 7×7 dinâmico, controlos interativos e resultados atualizados em tempo real. A orientação vertical mostra um aviso para rodar o dispositivo.
- Painéis de bónus à esquerda, energia e jackpot virtual à direita, controlos na parte inferior.
- Conserva o motor de cascatas, transformações e locução masculina robótica pré-gravada das versões anteriores.
- HTML autocontido: arte WebP e locuções MP3 incorporadas.

## Verificação
- Sintaxe JavaScript verificada com Node.js.
- Chromium em 844×390: 49 casas, rodada Turbo e transição para orientação vertical verificadas sem erros de JavaScript.
- Teste num iPhone físico com Safari ainda não realizado.

## Publicação
O código está em `Umbrella/Reactor-Rush/index.html`. O Vercel recebe manualmente o mesmo HTML. Não existe sincronização automática.


## V1.8 — Voz inglesa
- Nove gravações MP3 em inglês americano, com sintetização masculina grave e efeito metálico robótico.
- Mantém o grafismo horizontal HD, os menus em português e a lógica de jogo da V1.7.
- O botão de som e a pré-escuta no menu de informações mantêm-se.

## V1.9 — Locutor português maduro
- Nove anúncios MP3 em português de Portugal, voz masculina sintética grave e pausada, com efeito metálico reduzido.
- Mantém grafismo horizontal HD, lógica de jogo, efeitos sonoros e pré-escuta.


## V2.0 — música e mistura de áudio
- Banda sonora synthwave original, sintetizada localmente, em loop de 16 segundos.
- Quedas, encaixes, remoções e combinações com sons distintos e reforçados.
- Misturador de efeitos com compressão dinâmica; volumes iniciais da música 45% e efeitos 85%, ajustáveis no menu de informações.
- Música reduzida durante a locução portuguesa madura; recuperação automática após a fala.
- Silêncio ao desligar o som, ocultar a página ou rodar para modo vertical; reinício mediante interação.
- Grafismo, mecânica e ficheiros da locução da V1.9 preservados. Teste de audição no iPhone físico pendente.
