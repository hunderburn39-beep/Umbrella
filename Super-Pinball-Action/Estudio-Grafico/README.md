# Estúdio Gráfico — Super Pinball Action

Pré-visualização de quatro mesas reconstruídas estaticamente com os flippers originais da ROM, preservando posição, fotogramas e duas metades de sprite de cada conjunto.

## Abrir o visualizador
Em GitHub Pages, caso o repositório esteja configurado para publicar a raiz, abrir `Super-Pinball-Action/Estudio-Grafico/`. No computador, servir a raiz do repositório com `python -m http.server 8000` e abrir `http://localhost:8000/Super-Pinball-Action/Estudio-Grafico/`. Não se deve abrir o HTML diretamente por `file://` porque os PNG e JSON são carregados por caminhos relativos.

Controlos: botões Esquerdo e Direito, teclas A/D e setas ←/→; modo de fotograma fixo, seleção de paleta, mesa, composição estática, contornos de alinhamento e exportação PNG individual ou folha com sete fotogramas. O HTML carrega os PNG descomprimidos existentes em `../Assets`, sem duplicar imagens no repositório.

## Regenerar referências PNG
Instalar `Pillow` e executar `python Super-Pinball-Action/Estudio-Grafico/exportar_referencias.py`. Produz oito PNG em `Estudio-Grafico/Referencias/`: quatro mesas de fotograma zero e quatro folhas de sete fotogramas para comparação visual. Não substitui os originais. O script só lê os assets do GitHub.

## Metadados fidedignos
`flipper_layout.json` foi obtido da ROM US, SHA256 `8c139defd9b807c15872aee7e51a1fc57c8c1e4c20c764fa213d575140ca67c7`: oito linhas de posições em `0x12DA`, sete fotogramas por linha, seletores de mesa em `0x1EA8`, palavras de velocidade `0x4AAB` e `0x2CCD` na rotina de inicialização. Cada imagem de flipper tem duas peças 32 × 32 colocadas lado a lado. O raster da mesa resulta da rotação de 90° no sentido dos ponteiros do relógio da área bruta 512 × 224. **A paleta final em execução e a prioridade sprite/tile não foram validadas.**

Este visualizador não é o jogo completo. A simulação a 60 Hz e o número de chamadas por fotograma são escolhas de diagnóstico, não uma medição da cadência original. Não há física real da bola, sons sincronizados ou pontuação nesta bancada.

## HD a seguir
Trabalhar em `../Assets-HD/`, mantendo correspondência com os nomes e pontos de articulação das peças originais; não aplicar apenas filtros de escala nem alterar os PNG da ROM. Validar um conjunto de sete fotogramas de cada vez.


## Correção confirmada — posição dos flippers (21-11-2026)

Depois de auditar a ROM US (SHA256 `8c139defd9b807c15872aee7e51a1fc57c8c1e4c20c764fa213d575140ca67c7`), descobriu-se um erro no visualizador anterior: os grupos ímpares estavam classificados como esquerdo, mas aparecem fisicamente à direita depois da rotação do ecrã. Os grupos pares apareciam à esquerda e estavam classificados como direito.

**Correção aplicada:** seletores `2/4/6/8` → esquerdo; `1/3/5/7` → direito. O ficheiro `flipper_layout.json` (schema 2) contém agora `displayRect` calculado diretamente das coordenadas ROM: `x=208-rawY`, `y=rawX`, `w=32`, `h=64`. Foram preservadas as posições pixel-a-pixel de origem e os sete fotogramas de cada grupo. O erro corrigido é de associação de comando e de ausência de coordenadas pós-rotação explícitas, não um deslocamento arbitrário dos sprites.

**Prova na ROM:** a rotina de sprites `0x124c–0x12d6` escolhe as coordenadas/tile base e posiciona a segunda metade com `+32` no X e `+16` no índice de tile. A montagem intermediária `0x11c6` insere `0x0012` no campo tamanho/cor: cada metade corresponde a 4×4 tiles de 8 px, ou seja, 32×32. O MAME (Tecmo gaiden sprite renderer) também interpreta a posição de hardware como Y no quarto campo e X no quinto. A área visível antes de rodar é X=[0,511], Y=[16,239].

**Teste feito:** nos quatro mapas a alteração gráfica provocada pelo esquerdo pertence só à metade esquerda do ecrã; a do direito só à metade direita. O auditor local analisou 8 grupos, 56 combinações grupo-fotograma, 112 entradas sprite de duas metades e 8 cenas de mudança de lado.

**Pendente:** mistura BG/FG/sprites, prioridades e transparência, estados reais de RAM e teste visual por comparação fotograma-a-fotograma com a máquina. O Chromium deste ambiente bloqueou a abertura (`ERR_BLOCKED_BY_ADMINISTRATOR`), por isso não se reclama validação de navegador. Esta fase não significa que toda a composição da mesa esteja correta.

**Fontes de verificação externas:** [MAME spbactn.cpp](https://github.com/mamedev/mame/blob/master/src/mame/tecmo/spbactn.cpp) e [tecmo_spr.cpp](https://github.com/mamedev/mame/blob/master/src/mame/shared/tecmo_spr.cpp).
