# Catálogo de assets — Super Pinball Action

Catálogo de **1.302 ficheiros PNG** localizados em `../Assets/`; preserva os originais e não contém filtros de HD. Funciona com a estrutura de pastas do repositório.

## Abrir
- Se o GitHub Pages do repositório publicar a pasta raiz, abrir `/Super-Pinball-Action/Catalogo/`.
- Para utilização local, iniciar um servidor na raiz do clone: `python -m http.server 8000` e abrir `http://localhost:8000/Super-Pinball-Action/Catalogo/`.
- Abrir `index.html` directamente pelo disco (`file://`) pode falhar, pois o navegador bloqueia a leitura de `manifest.json`; usar o servidor local.
- A página lista apenas **1.302 assets organizados**; os **61.378 PNG** de `Sprites/PNG` podem ser vistos diretamente na árvore do GitHub.

## Funcionalidades
Pesquisa por nomes/IDs, categorias, banco de cor, zoom, paginação para poupar memória, variantes da mesma imagem em diferentes bancos, seleção de ficheiros para redesenhar, exportação CSV. Nenhuma alteração aos PNG originais.

## Atualizar a biblioteca
Se alterares os assets originais (não aconselhado), executar:
`python Super-Pinball-Action/Catalogo/rebuild_manifest.py`

O script exige 1.302 PNGs e falha com contagens divergentes, evitando publicar um catálogo incompleto. Os ficheiros devem ser colocados em `Assets-HD/` quando redesenhados, não sobre os originais.

Nota: a relação entre paletas, modos da máquina, efeitos e identidade dos objetos ainda necessita de validação contra a ROM. O catálogo é uma ferramenta de curadoria, não prova de fidelidade total do motor.