#!/usr/bin/env python3
"""Generate unfiltered original flipper reference PNGs from ROM-derived Assets.

Run from any working directory:
  python Super-Pinball-Action/Estudio-Grafico/exportar_referencias.py

Requires Pillow. Original PNG assets must already exist in Assets/;
does not overwrite originals or publish images automatically.
"""
import json
from pathlib import Path
from PIL import Image

here=Path(__file__).resolve().parent
root=here.parent
assets=root/"Assets"
layout=json.loads((here/"flipper_layout.json").read_text(encoding="utf-8"))
out=here/"Referencias"
out.mkdir(exist_ok=True)

def asset(path):
    p=assets/path
    if not p.is_file():raise FileNotFoundError(p)
    with Image.open(p) as im:
        return im.convert("RGBA")

def tile(base,bank):
    return asset(f"04_Flippers/bank{bank}/tile_{base:05d}_0x{base:04X}.png")

def compose(map_index,bank,left,right):
    table=asset(f"02_Mesas/map_{map_index}/mixed_palette{bank}.png")
    if table.size!=(224,512):raise ValueError(f"Unexpected table size {table.size}")
    raw=Image.new("RGBA",(512,224))
    for selector in layout["maps"][map_index]["selectors"]:
        row=layout["rows"][selector-1]
        frame=left if row["channel"]=="left" else right
        base=row["frameBases"][frame]
        x,y=row["rawX"],row["rawY"]-16
        for half in range(2):
            image=tile(base+16*half,bank)
            if image.size!=(32,32):raise ValueError("Flipper tile is not 32 x 32")
            raw.alpha_composite(image,(x+32*half,y))
    table.alpha_composite(raw.transpose(Image.Transpose.ROTATE_270))
    return table

def main():
    for map_index in range(4):
        bank=0
        contact=Image.new("RGBA",(224*7,512))
        for frame in range(7):
            image=compose(map_index,bank,frame,frame)
            contact.alpha_composite(image,(frame*224,0))
            if frame==0:
                image.save(out/f"mesa_{map_index+1}_banco_0_frame_0.png",optimize=True)
        contact.save(out/f"mesa_{map_index+1}_banco_0_7_fotogramas.png",optimize=True)
    print("Exportadas 4 mesas + 4 folhas PNG com sete fotogramas cada.")

if __name__=="__main__":main()
