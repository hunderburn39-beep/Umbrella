# Super Pinball Action — Assets PNG

✅ **Biblioteca gráfica publicada em pastas, sem ficheiros ZIP na árvore atual.**

## Assets organizados (1.302 PNG)

- `01_Folhas_e_paletas/`: 66 PNG
- `02_Mesas/`: 76 PNG das quatro mesas e variantes de paleta
- `03_Animacoes/`: 920 PNG de fragmentos e sequências
- `04_Flippers/`: 224 PNG de fotogramas
- `04_Bolas/`: 16 PNG

## Sprites individuais (61.378 PNG)

Em `../Sprites/PNG/`:
- `release/`: 38.179 PNG
- `prototype/`: 23.191 PNG
- `palettes/`: 8 PNG

**Total de ficheiros PNG publicados: 62.680.** Contagem confirmada através das árvores Git remotas em 20-11-2026. Os 36 CSV temporários de importação foram removidos da árvore atual após validação automática. A ROM e os ZIP originais não foram incluídos.

Os PNG derivam da ROM fornecida pelo utilizador. Algumas paletas são de diagnóstico e ainda não traduzem necessariamente o estado de cor durante a execução. A organização em grupos de sprites não significa que todos os objetos ou animações completos estejam identificados.

## Regenerar a partir da ROM local

O exportador `../importar_png.py` permite reconstruir as pastas a partir dos ZIP já gerados. O fluxo `.github/workflows/importar-assets-spa.yml` valida o hash de cada PNG importado e limpa os ficheiros temporários após o commit.

A utilização e distribuição de elementos gráficos extraídos da ROM estão sujeitas aos direitos aplicáveis.
