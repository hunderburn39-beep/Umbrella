#!/usr/bin/env python3
"""Reconstruct 8x HD flipper sprites from original ROM PNGs, preserving tile/frame IDs."""
from pathlib import Path
from PIL import Image
import cv2, json, hashlib
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Assets'/'04_Flippers'/'bank0'
DEST=ROOT/'Assets-HD'/'04_Flippers'
S=8
COLORS={
  (119,0,0):0,(255,85,85):1,(102,68,102):2,(68,68,68):2,
  (119,153,153):3,(68,187,187):3,(0,255,255):3,(17,221,221):3,
  (153,255,255):4,(170,255,255):4,(187,255,255):4,(204,255,255):4,
  (221,255,255):4,(238,255,255):4,(255,255,255):4,
}
METAL=np.asarray([(109,10,27),(251,73,83),(68,48,68),(44,215,232),(229,252,254)],dtype='float32')

def vector(binary):
    h,w=binary.shape
    pad=2
    up=cv2.resize(np.pad(binary.astype('uint8')*255,pad),None,fx=S,fy=S,interpolation=cv2.INTER_NEAREST)
    smooth=cv2.GaussianBlur(up,(0,0),S*.36)
    paths,hierarchy=cv2.findContours((smooth>=121).astype('uint8'),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    canvas=np.zeros_like(up)
    if hierarchy is not None:
        for idx,path in enumerate(paths):
            if hierarchy[0,idx,3]!=-1: continue
            cv2.drawContours(canvas,[path],-1,255,-1,cv2.LINE_AA)
            child=hierarchy[0,idx,2]
            while child!=-1:
                cv2.drawContours(canvas,[paths[child]],-1,0,-1,cv2.LINE_AA)
                child=hierarchy[0,child,0]
    return canvas[pad*S:(pad+h)*S,pad*S:(pad+w)*S]

def read_frame(base):
    canvas=Image.new('RGBA',(64,32))
    for half in (0,1):
        tile=base+16*half
        name=f'tile_{tile:05d}_0x{tile:04X}.png'
        with Image.open(SOURCE/name) as image:
            if image.size!=(32,32):raise ValueError(f'Original tile invalid: {name}')
            canvas.alpha_composite(image.convert('RGBA'),(32*half,0))
    return np.asarray(canvas)

def redraw(original):
    h,w=original.shape[:2]
    shape=(h*S,w*S)
    mask=original[:,:,3]>0
    material=np.full((h,w),-1,dtype='int16')
    for color,category in COLORS.items():
        material[((original[:,:,:3]==color).all(axis=2))&mask]=category
    if np.any(material[mask]<0):
        raise ValueError('Original ROM palette has unknown colours')
    outer=vector(mask)
    weights=np.zeros(shape,dtype='float32')
    rgb=np.zeros((*shape,3),dtype='float32')
    yy,xx=np.mgrid[:shape[0],:shape[1]].astype('float32')
    nx=xx/shape[1]
    ny=yy/shape[0]
    for k,color in enumerate(METAL):
        region=vector(material==k).astype('float32')/255
        light=.90+.14*np.cos((ny-.18)*np.pi*.88)+.045*np.sin(nx*8.5)
        if k==3:light+=.05*np.sin(ny*13)
        rgb+=color[None,None,:]*light[:,:,None]*region[:,:,None]
        weights+=region
    fallback=cv2.resize(material.astype('float32'),(shape[1],shape[0]),interpolation=cv2.INTER_NEAREST).astype('int16')
    fallback=np.clip(fallback,0,len(METAL)-1)
    rgb=np.where(weights[:,:,None]>.008,rgb/np.maximum(weights[:,:,None],.001),METAL[fallback])
    distance=cv2.distanceTransform((outer>70).astype('uint8'),cv2.DIST_L2,3)
    normal=np.pad(distance[1:]-distance[:-1],((0,1),(0,0)))
    bevel=np.exp(-(distance/(S*.75))**2)
    rgb+=np.clip(-normal,0,1)[:,:,None]*bevel[:,:,None]*25
    rgb-=np.clip(normal,0,1)[:,:,None]*bevel[:,:,None]*17
    return np.dstack([np.clip(rgb,0,255),outer]).astype('uint8')

def main():
    count=0
    report=[]
    for base_group in (512,768,2048,2304):
        for frame in range(7):
            base=base_group+frame*32
            original=read_frame(base)
            hd=redraw(original)
            for half in (0,1):
                tile=base+half*16
                original_half=original[:,half*32:(half+1)*32,3]>127
                hd_half=hd[:,half*32*S:(half+1)*32*S,:]
                check=cv2.resize(hd_half[:,:,3],(32,32),interpolation=cv2.INTER_AREA)>127
                if not np.array_equal(original_half,check):
                    raise ValueError(f'Geometry changed for tile {tile}')
                for bank in range(4):
                    folder=DEST/f'bank{bank}'
                    folder.mkdir(parents=True,exist_ok=True)
                    filename=folder/f'tile_{tile:05d}_0x{tile:04X}.png'
                    Image.fromarray(hd_half,'RGBA').save(filename,optimize=True)
                    count+=1
            report.append({'group':base_group,'frame':frame,'baseTile':base})
    if count!=224: raise ValueError(f'Unexpected PNG count {count}')
    for bank in range(4):
        files=list((DEST/f'bank{bank}').glob('*.png'))
        if len(files)!=56:raise ValueError('Missing frame in HD bank')
        for path in files:
            with Image.open(path) as image:
                if image.size!=(256,256) or image.mode!='RGBA':
                    raise ValueError(f'Invalid output {path}')
    (ROOT/'Assets-HD'/'flippers_hd_report.json').write_text(
       json.dumps({'scale':S,'files':count,'distinctFrames':28,'tileIds':56,
                   'method':'vector contours and authored chrome highlights',
                   'unchangedCollisionPixels':True,'frames':report},indent=2))
    print(f'Generated and validated {count} HD PNGs, 56 tile IDs at 8x')

if __name__=='__main__':main()
