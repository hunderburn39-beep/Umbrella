#!/usr/bin/env python3
"""Repaint the four original ROM ball sprite tiles at 8x, preserving exact hit pixels."""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image
from gerar_flippers_hd import redraw

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Assets'/'04_Bolas'
DEST=ROOT/'Assets-HD'/'04_Bolas'
TILES=(0x50,0x60,0x70,0x80)

def main():
    report=[]
    for tile in TILES:
        name=f'tile_{tile:05d}_0x{tile:04X}.png'
        with Image.open(SOURCE/'bank0'/name) as img:
            if img.size!=(32,32):raise ValueError(f'Wrong ROM tile size: {name}')
            original=np.asarray(img.convert('RGBA'))
        hd=redraw(original)
        if hd.shape!=(256,256,4):raise ValueError('HD dimensions changed')
        mask=cv2.resize(hd[:,:,3],(32,32),interpolation=cv2.INTER_AREA)>127
        if not np.array_equal(mask,original[:,:,3]>127):
            raise ValueError(f'Ball collision silhouette changed for {name}')
        for bank in range(4):
            with Image.open(SOURCE/f'bank{bank}'/name) as ref:
                reference=np.asarray(ref.convert('RGBA'))
            if not np.array_equal(reference,original):
                raise ValueError(f'Bank {bank} has a different original ball graphic')
            dest=DEST/f'bank{bank}'
            dest.mkdir(parents=True,exist_ok=True)
            Image.fromarray(hd,'RGBA').save(dest/name,optimize=True)
        report.append({'tile':tile,'size':[256,256],'originalOpaquePixels':int((original[:,:,3]>127).sum()),'maskMatched':True})
    files=list(DEST.rglob('*.png'))
    if len(files)!=16:raise ValueError(f'Expected 16 HD ball PNGs, got {len(files)}')
    (ROOT/'Assets-HD'/'bolas_hd_report.json').write_text(json.dumps(report,indent=2))
    print('Generated 16 HD ball PNGs with exact original 32x32 silhouettes')

if __name__=='__main__':main()
