# Sprites — Super Pinball Action

Independent PNG export from the supplied merged ROM set, with stable original tile IDs.

Local output: **61,312 PNGs**: 53,248 decoded cells (including empty slots) and 8,064 possible composite groups (16×16, 32×32, 64×64). The US and Japan share the release graphics; separate prototype regions are included. The local export was verified by reopening each PNG and comparing hashes of its indexed pixels.

Run from the parent Super-Pinball-Action directory:
```sh
python -m pip install Pillow
python extract.py spbactn.zip extracted
python Sprites/export_sprites.py extracted Sprites.zip
```

Folder structure: release/{sprites,fg,bg}, prototype/{sprites,fg,bg,extra}, palettes, catalog.csv and manifest.json. Individual PNGs use original pen indices, diagnostic grayscale and transparent pen 0. Eight static palette banks are exported separately; runtime palette assignments and complete named objects have not yet been verified. Prototype background decoding remains uncertain.

This public repository contains the reproducible exporter, not the generated PNG archive. Use the supplied local ROM to generate it.
