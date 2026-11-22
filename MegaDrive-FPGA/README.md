# Umbrella Mega Drive FPGA V0.1
Estado: integração inicial reproduzível; compilação e ensaios físicos pendentes.

## Plataforma
DE10-Nano / Cyclone V, ambiente MiSTer. O ARM trata do menu e carregamento da ROM; os circuitos de jogo são implementados em lógica programável FPGA. Não é um emulador de CPU executado no ARM. Não é ainda uma PCB autónoma.

## Dependência de hardware digital
Base: https://github.com/MiSTer-devel/MegaDrive_MiSTer
Revisão fixada: 8f2716f48818c84e9677cd2526cee39fa958920e
Engenharia reversa: https://github.com/nukeykt/Nuked-MD-FPGA
Preservar os créditos e licenças originais de cada componente. Ao redistribuir binários, cumprir as obrigações aplicáveis de disponibilização do código-fonte correspondente. Não inclui ROMs comerciais.

## Preparar e compilar
Num PC com Git e Bash:
    bash build.sh prepare

Num PC com Quartus Prime compatível com Cyclone V (projeto upstream declara 17.0.2 Standard):
    bash build.sh build

Saída esperada: dist/Umbrella_MegaDrive_FPGA.rbf. O ficheiro só é criado após compilação concluída. Rever relatórios de utilização e temporização.

## Instalação de teste
Copiar a RBF para a instalação MiSTer no cartão SD. Colocar ROMs legitimamente obtidas na pasta MegaDrive indicada pela configuração MiSTer. Arrancar o core pelo menu. A necessidade de expansão SDRAM depende da configuração upstream.

## Plano de aceitação
1. Quartus: análise, síntese, fitter e TimeQuest; confirmar margens de temporização.
2. 68000: vetores de reset, interrupções, operações e ciclos de bus.
3. Z80: reset, BUSREQ/BUSACK, acesso à RAM e áudio.
4. VDP: DMA, sprites, scrolling, prioridade, interrupções, PAL/NTSC.
5. YM3438/PSG: temporização, registos, frequências e saída estéreo.
6. Memória: RAM principal 64 KiB, VRAM 64 KiB e RAM Z80 8 KiB.
7. Cartucho: ROM, SRAM, EEPROM, comandos de 3/6 botões.
8. Comparar imagem, áudio e traces de bus com a consola física e ROMs de diagnóstico legalmente obtidas.

A base Nuked usa uma combinação de chips aproximada à VA7, não uma cópia exata de uma revisão comercial. A placa física própria e a entrada de cartuchos originais ficam para depois da validação.

## Estado real
- Referência RTL e revisão identificadas.
- Script de preparação e compilação publicado.
- Síntese, bitstream e hardware: não verificados.
