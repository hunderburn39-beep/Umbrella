# Reactor Rush — V1.5

🎰 **[Jogar online](https://reactor-rush-umbrella.vercel.app/)**

Protótipo HTML5 autónomo de slot de cascatas com **créditos fictícios**, otimizado para telemóveis. Não há depósitos, levantamentos, prémios com valor real nem RTP certificado. O jogo não reproduz a arte, o código, o áudio ou a matemática da Play’n GO.

## Mecânicas

- Grelha 7×7, grupos de cinco ou mais símbolos ligados horizontal ou verticalmente.
- Wilds que só são contabilizados uma vez por cascata, fusões visuais 2×2 e multiplicador de cascatas até ×5.
- Gravidade animada: símbolos desaparecem e os restantes caem por coluna.
- Energia quântica em cinco cargas; ativa Implosão, Mutação, Demolição ou Diagonais.
- Em cada quinta ativação quântica, o Gigante transforma um quadrado 3×3 em Wilds e atribui prémio virtual. O jackpot virtual pode substituir esse prémio com probabilidade de 1/80 por evento gigante.
- Turbo, Auto ×10, som sintetizado opcional, créditos gratuitos e gravação local de saldo e recordes.

## Novidades da V1.4

- **Transformações quânticas por vagas**, mostrando em vez de ocultar as mudanças no tabuleiro.
- **Gigante 3×3 revelado em três linhas** e o prémio é creditado depois da transformação.
- Indicador **"GIGANTE EM N ATIVAÇÕES"** junto ao medidor quântico.
- **Efeitos de revelação e pulsação** com animações CSS leves; reduzidos automaticamente quando o sistema pede movimento reduzido.
- **Dois planos de efeitos separados**: mensagens de bónus não apagam pop-ups de prémios.
- Melhor desempenho do medidor: as cinco luzes persistem em vez de serem reconstruídas a cada atualização.
- Historial do último tipo de bónus e total de ativações na janela de regras.
- Proteção de mutação em tabuleiros sem cores normais e seleção da Implosão sem repetições.

## Validação

- Testes automatizados no Chromium com larguras 320, 375, 390 e 428 px, sem rolagem horizontal.
- Quatro bónus normais e evento gigante exercitados; 49 nós de símbolo e cinco luzes persistentes verificados.
- 2.000 grelhas aleatórias verificadas, Auto ×10 e 20 rodadas Turbo; sem erros JavaScript detetados.
- O Safari físico no iPhone **ainda não foi testado**.

## Publicação

Código-fonte: `index.html`, autocontido e sem dependências. A versão pública está hospedada no Vercel e é publicada **manualmente** a partir do mesmo HTML de `Umbrella/Reactor-Rush`; não existe sincronização automática entre GitHub e Vercel.

## V1.5 — locutor em português
- Voz sintetizada pelo navegador (preferência por português de Portugal, se instalada).
- Avisos de ativação do som, transformações quânticas, Gigante e jackpot virtual.
- Apenas uma fala de cada vez, prioridades de locução e cancelamento ao silenciar ou ocultar a página.
- Opção de locutor independente no painel de informações. O botão de som desativa também a voz.
- A disponibilidade e o timbre dependem do dispositivo. A matemática e os prémios da V1.4 não foram alterados.
