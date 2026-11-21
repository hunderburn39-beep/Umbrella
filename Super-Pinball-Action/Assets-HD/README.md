# Assets-HD — reconstrução gráfica não destrutiva

Esta pasta serve para os novos desenhos HD de Super Pinball Action. **Não substituir os PNG da ROM** em `../Assets/` ou `../Sprites/PNG/`.

Convenção de nomes: preservar identificador e número do fotograma no nome, por exemplo `04_Flippers/bank0/tile_00512_0x0200.png`; os ficheiros HD devem ser guardados com a mesma subpasta relativa que a origem, de forma a permitir troca por caminho.

## Fluxo de trabalho
1. Selecionar originais em `../Catalogo/index.html` (exportação CSV).
2. Redesenhar os assets em resolução maior, preservando transparência, enquadramento, orientações e pontos de articulação.
3. Exportar os novos PNG para esta pasta mantendo caminho relativo e geometria identificável.
4. Validar animações completas em conjunto e comparar com a ROM antes de integrar no jogo.

Não aplicar apenas filtros para chamar HD. O novo asset deve ser efetivamente redesenhado. As associações finais de paleta, geometria e estados ainda precisam de confirmação.