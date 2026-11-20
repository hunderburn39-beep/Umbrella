# Sprites — Super Pinball Action

✅ **61.378 PNG extraídos da ROM já publicados, individualmente e descomprimidos, em `PNG/`.**

Distribuição verificada no GitHub:
- `PNG/release/`: 38.179
- `PNG/prototype/`: 23.191
- `PNG/palettes/`: 8

O exportador conserva IDs originais de tiles e inclui células 8×8/16×8, grupos compostos 16×16/32×32/64×64, folhas e bancos de paletas de diagnóstico. A contagem original de 61.312 células e grupos foi complementada com folhas e paletas para totalizar 61.378 PNG.

Para regenerar a partir da ROM local (não armazenada neste repositório):

```sh
python -m pip install Pillow
python extract.py spbactn.zip extracted
python Sprites/export_sprites.py extracted Sprites.zip
```

A pasta `../Assets/` contém mais 1.302 PNG organizados para produção, incluindo mesas, flippers, bolas e animações. Total conjunto publicado: **62.680 PNG**. As cores de diagnóstico e o protótipo podem requerer investigação adicional antes de serem usados como apresentação fiel do jogo.

Todos os PNG foram importados com validação de hashes pelo fluxo GitHub Actions `importar-assets-spa.yml`. Os CSV de transferência foram eliminados da árvore atual após o commit; nem os ficheiros ZIP nem a ROM foram adicionados ao repositório.
