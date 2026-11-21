# Assets-HD — reconstrução gráfica não destrutiva

Os PNG originais extraídos da ROM permanecem em `../Assets/` e `../Sprites/PNG/` e **nunca são alterados pelo gerador HD**.

## Flippers HD — versão gráfica 1

- `04_Flippers/bank0..bank3/`: **224 PNG individuais** de 256 × 256 píxeis RGBA, escala 8× face aos 32 × 32 originais.
- Quatro grupos geométricos × sete fotogramas × duas metades por sprite × quatro bancos.
- IDs, subpastas e metades de sprite são idênticos aos originais, para troca de asset sem alterar posições.
- Fonte: `../Assets/04_Flippers/bank0/`. Os bancos originais têm os mesmos píxeis nesta extração; as quatro cópias HD mantêm essa correspondência.
- Gerador: `gerar_flippers_hd.py`; usa contornos vetoriais derivados das regiões de cores originais e um material metálico definido em código. **Não é mera ampliação por filtro.**
- O teste de máscara assegura que os 56 tiles distintos voltam ao mesmo conjunto de píxeis ocupados quando o PNG HD é reduzido à resolução original.

**Não são ainda assets finais aprovados**: cor, brilho e integração com a cena em movimento dependem de validação visual. A paleta durante a execução da ROM e a ordem das camadas permanecem por validar.

## Bolas HD — versão gráfica 1

- `04_Bolas/bank0..bank3/`: **16 PNG individuais** de 256 × 256 píxeis (quatro formas originais × quatro bancos).
- Gerador: `gerar_bolas_hd.py`, partilha as rotinas de contornos com o gerador dos flippers.
- Os 16 ficheiros foram validados contra as máscaras originais de 32 × 32, sem alteração da silhueta ocupada.
- **Total nesta primeira versão: 240 PNG HD descomprimidos**, incluindo 224 dos flippers e 16 da bola. Nenhum PNG da ROM foi substituído.

## Verificar e comparar

- Abrir o visualizador `../Comparador-HD/index.html` através de servidor local ou GitHub Pages (quando ativado).
- Comparar em simultâneo as quatro mesas, quatro bancos, sete posições de flipper, incluindo a zona ampliada.
- Para regenerar com Python: `python -m pip install pillow numpy opencv-python-headless` e `python Super-Pinball-Action/Assets-HD/gerar_flippers_hd.py`.
- GitHub Actions: `.github/workflows/spa-flippers-hd.yml` (geração e commit automático dos 240 PNG descomprimidos). As duas execuções de produção de 21/11/2026 foram concluídas com sucesso.

## Trabalhos seguintes

Conservar transparência, limites de colisão e sete fotogramas, sem mudar a mecânica; rever efeitos de luz no motor, bolas e elementos de mesa. A reconstrução física do jogo ocorre separadamente na pasta Mecanica.