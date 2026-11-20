# Assets originais — Super Pinball Action
240 PNGs já enviados e confirmados na árvore Git: 16 bolas e os 224 PNGs de flippers (56 em cada um dos quatro bancos). Os SHA Git correspondem aos ficheiros extraídos. A biblioteca completa contém 62.680 PNGs e ainda não foi enviada em lote.

## Importação por Git bundle local
Num clone atualizado do UMBRELLA, com a árvore de trabalho limpa, executar:
```sh
git fetch /caminho/Super_Pinball_Action_Assets.gitbundle refs/heads/assets-import
git merge --allow-unrelated-histories --no-edit FETCH_HEAD
git push origin main
```
Ficheiro bundle SHA256: 8cd0f2ea284dc3568d864fdc66a11892f2761c4b19a5fd505e54253e9421df1c. Integração testada num repositório local com os 72 PNG já existentes e código separado; 62.680 PNG finais, sem conflitos no teste. O bundle não é colocado no GitHub.

## Alternativa: importador dos pacotes locais
```sh
python Super-Pinball-Action/importar_png.py /caminho/Super_Pinball_Action_Sprites.zip /caminho/Super_Pinball_Action_Assets_PNG.zip
git add Super-Pinball-Action/Sprites/PNG Super-Pinball-Action/Assets
git commit -m "Import original PNG sprites and assets"
git push origin main
```
61.378 PNGs em Sprites/PNG e 1.302 PNGs em Assets. Paletas de diagnóstico e variantes ainda requerem associação ao estado original. Usar apenas materiais com autorização de distribuição.
