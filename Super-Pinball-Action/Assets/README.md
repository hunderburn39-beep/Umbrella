# Assets originais — Super Pinball Action
Quatro PNGs de bola (banco 0) já estão nesta pasta; os SHA Git foram confirmados contra o ZIP original.
A biblioteca completa ainda não foi enviada em lote.

Para importar os dois pacotes locais verificados, num clone Git do UMBRELLA com Python 3.9+:
```sh
python Super-Pinball-Action/importar_png.py /caminho/Super_Pinball_Action_Sprites.zip /caminho/Super_Pinball_Action_Assets_PNG.zip
git add Super-Pinball-Action/Sprites/PNG Super-Pinball-Action/Assets
git commit -m "Import original PNG sprites and assets"
git push origin main
```
Importador testado localmente: 61.378 PNGs em Sprites/PNG (inclui folhas e paletas), 1.302 PNGs em Assets, mais os catálogos e metadados. Os ZIPs não são copiados. Paletas de diagnóstico e variantes ainda requerem associação ao estado original. Usar apenas materiais com autorização de distribuição.
