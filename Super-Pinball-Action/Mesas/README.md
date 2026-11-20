# Fase 4 — Mesas originais
Executar após extract.py com a ROM local: `python Mesas/maps.py extracted Mesas/results` (Pillow, numpy).
Reconstrução estática da versão US: quatro mapas, 4096 células de fundo, 2131 colocações de primeiro plano; 76 PNG em 224×512, quatro arrays de 32×32 por mesa em BIN e JSON. Não inclui imagens ou ROM no repositório público.
- 1512–15B4: fundo; seletor 2,0,1,3 em 15D6; tabelas de coordenadas 15B6/15C6. Quatro blocos de 256 células, incremento do byte alto em 155C. Atributos 31BDC + 896×seletor.
- 15DA–163A: offsets relativos a 2FB5E, ponteiro absoluto seguido de 28 máscaras de 32 bits, bits 31→0 selecionam o próximo ID. Atributos relativos a 2FB56. Os fluxos terminam em 30912, 2FF52, 303E8, 30DDC.
- 2B64–2BF2: atualização integral da paleta em oito blocos de 256 palavras, destinos 81000,81400,81600,80600,80000,82200,82000,80400; normal FG/BG em offsets 100/200 do banco, aditivo FG/BG em 500/300. Bit 3 do atributo FG marca mistura. O código exporta quatro bancos de teste, não determina a seleção em execução.
- A geometria foi verificada com os limites das tabelas e os índices gráficos. Sprites móveis, HUD, efeitos em tempo real, colisões e cores finais carecem de confirmação.
Referências: MAME src/mame/tecmo/spbactn.cpp e tecmo_mix.cpp (BSD-3-Clause, David Haywood).