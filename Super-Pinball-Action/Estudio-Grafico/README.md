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


## V0.5 — composição estática com máscara OAM (21-11-2026)

Foi adicionado o modo **Mesa ROM + máscara OAM** como seleção inicial do estúdio. Em vez de perder a mistura de cores pré-calculada da mesa, este modo usa a imagem `mixed_paletteN.png` original da extração, desenha os flippers de prioridade 1 apenas nas zonas não opacas do primeiro plano e sobrepõe os de prioridade 3. A máscara vem da transparência de `foreground_paletteN.png`; não são alterados nem redesenhados os PNG extraídos.

A rotina lê e valida agora as **56 entradas** de `oam_auditoria.json`, que contêm **112 peças** de sprite, incluindo tiles, coordenadas, dimensões e prioridade. Existem duas prioridades base na ROM: `0x14` (prioridade 1, atrás do FG) e `0x34` (prioridade 3, à frente do FG). Os modos antigos permanecem acessíveis para comparação e o modo **Apenas flippers** permite avaliar as orientações dos sete fotogramas sem as ilustrações da mesa.

Foi confirmada através da árvore GitHub a presença dos **272 PNG** exigidos pelo estúdio para estas vistas: 224 flippers (56 por paleta, quatro paletas) e 48 imagens de composição de mesa (4 mesas × 4 paletas × 3 camadas). A verificação é reproduzível depois de descarregar/clonar o repositório:

```sh
node Super-Pinball-Action/Estudio-Grafico/validar_v05.mjs
```

**Limite técnico importante:** o modo com máscara preserva a mistura da imagem estática, mas não calcula corretamente os píxeis em que um flipper de prioridade 1 colide com um primeiro plano de mistura aditiva/translúcida. Para isso é necessário reproduzir, por píxel, os índices de cor, os bits de mistura e a paleta efetivamente ativa. A prioridade base não equivale à validação do compositor inteiro em tempo de execução. O browser também não foi validado visualmente nesta sessão; a verificação atual cobre a sintaxe JavaScript, os metadados OAM e a existência dos ficheiros necessários.


## V0.6 — localizar misturas gráficas ainda incertas (21-11-2026)

O visualizador conserva a seleção dos quatro mapas, paletas, prioridades OAM e sete fotogramas originais de cada flipper. O novo modo de **auditoria de mistura** é ativado pela caixa “Assinalar sobreposições incertas”, apenas sobre a composição `Mesa ROM + máscara OAM`. As intersecções suspeitas são marcadas a magenta, sem alterar os PNG e com contagem de píxeis no estado da mesa.

**Método:** compor separadamente os sprites que têm prioridade base 1, comparar por píxel `mixed_paletteN.png` e `combined_paletteN.png` nas zonas com primeiro plano opaco em `foreground_paletteN.png`, e assinalar apenas onde haja simultaneamente sprite e diferença RGB. O algoritmo está isolado em `mixer_auditoria.js`. Esta é uma inspeção *heurística* dos PNG de diagnóstico: algumas diferenças não significam necessariamente mistura de hardware e cores idênticas podem ocultar alguns casos. A máscara V0.5 continua a ser a base de visualização; o overlay novo **não** simula corretamente a mistura dinâmica.

A leitura dos atributos foi reconfirmada com o pipeline de sprites Tecmo: `0x14` → prioridade 1; `0x34` → prioridade 3, após inserção no endereço de cor e multiplicação pela granularidade de 16 píxeis. A prioridade efetiva observada pelo mixer é `(sprpixel >> 8) & 3`; a mistura do sprite utiliza `(sprpixel >> 10) & 1`. O bit `0x40` pode ser acrescentado em execução e não é deduzido do atributo base. A interface mostra a prioridade e o indicador `blendBase` de cada flipper.

**Verificações:**

```sh
node Super-Pinball-Action/Estudio-Grafico/validar_v05.mjs
node Super-Pinball-Action/Estudio-Grafico/validar_v06.mjs
```

A auditoria sintética V0.6 cobre o mapa de colisão RGBA, atributos das 112 peças e sintaxe do JavaScript. A observação visual num navegador real e a comparação com capturas da máquina permanecem pendentes. A reprodução exata do mixer exige o mapa FG com bits de mistura, as paletas de execução completas e o estado do atributo `0x40`, além dos sprites dinâmicos da bola e das cancelas. Referências: [Tecmo spr](https://github.com/mamedev/mame/blob/master/src/mame/shared/tecmo_spr.cpp), [Tecmo mix](https://github.com/mamedev/mame/blob/master/src/mame/tecmo/tecmo_mix.cpp), [spbactn](https://github.com/mamedev/mame/blob/master/src/mame/tecmo/spbactn.cpp).


## V0.7 — comparação por lado e prova OAM exportável (21-11-2026)

O estúdio permite exportar folhas com **sete fotogramas** de três formas: `Esquerdo + direito`, `Só esquerdo (direito parado)` e `Só direito (esquerdo parado)`. O lado não escolhido mantém a posição que tinha no momento de carregar no botão de exportação. Isto permite estudar cada flipper sem a interferência do outro comando; não altera coordenadas nem sprites originais.

A opção **Relatório OAM em JSON** cria um ficheiro para a mesa e paleta selecionadas, com o hash da ROM, os seletores de flippers, as posições na ROM e no ecrã, os identificadores das duas peças 32×32, os fotogramas e os bits base de prioridade, mistura e espelhamento. O relatório conserva a informação de sete estados de cada grupo efetivamente presente na mesa. Isto **não é uma captura da sprite RAM em execução**; descreve a reconstrução estática verificada contra as tabelas da ROM.

Além da verificação de `rawX/rawY`, o início do estúdio verifica agora que os retângulos de ecrã de cada entrada OAM batem certo com `flipper_layout.json` (após rotação). Se houver divergência, falha explicitamente em vez de desenhar peças deslocadas silenciosamente.

Testes reproduzíveis:

```sh
node Super-Pinball-Action/Estudio-Grafico/validar_v05.mjs
node Super-Pinball-Action/Estudio-Grafico/validar_v06.mjs
node Super-Pinball-Action/Estudio-Grafico/validar_v07.mjs
```

O V0.7 verifica 48 combinações (4 mesas × 4 paletas × 3 modos), 336 fotogramas e 1092 grupos de sprites representados, além da sintaxe do JavaScript. Estes testes são **de dados e de lógica**, não substituem o teste de imagem no navegador. Para abrir o estúdio do GitHub Pages são precisos os ficheiros de ajuda `mixer_auditoria.js` e `frame_auditoria.js` ao lado de `index.html`.
