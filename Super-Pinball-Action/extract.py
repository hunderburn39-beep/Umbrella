#!/usr/bin/env python3
"""Decode user-supplied merged spbactn.zip (Python 3 + Pillow).
Layout reference: MAME src/mame/tecmo/spbactn.cpp, BSD-3-Clause, David Haywood.
No original ROM bytes included. Usage: python extract.py spbactn.zip extracted
"""
import sys,zipfile,hashlib,json,struct,wave,math
from pathlib import Path
from PIL import Image
z=zipfile.ZipFile(sys.argv[1]); out=Path(sys.argv[2] if len(sys.argv)>2 else 'extracted')
assert z.testzip() is None
expected='57f4c503 87427d7d b648a40a 0172d79a 862ebacd 1cc1379a 315eab4d 7b76efd9 6741bd3f 488cc511 9577b48b b5b2d824 e8250c26 2297a725 3a0c70ed 445fc2c5 c9860ae9 40f6a1e6 8226f644 ce31871e 02b69ab9 37922110 9d6ef9ab 6953fd62 b4123511 cd6ba360 86406336 2c54354a'.split()
assert sorted(f'{x.CRC:08x}' for x in z.infolist())==sorted(expected)
def put(n,b):
    p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def inter(a,b):
    r=bytearray(len(a)*2);r[::2]=a;r[1::2]=b;return bytes(r)
r=z.read;p='spbactnp/'
m={'files':[],'graphics':{},'samples':[],'vectors':{}}
for x in z.infolist():
    b=r(x.filename);put('rom_original/'+x.filename,b)
    m['files'].append(dict(name=x.filename,bytes=len(b),crc32=f'{x.CRC:08x}',sha1=hashlib.sha1(b).hexdigest(),sha256=hashlib.sha256(b).hexdigest()))
for name,b in {'us':inter(r('rom1.bin'),r('rom2.bin')),'jp':inter(r('spbactnj/a-u68.1'),r('spbactnj/a-u67.2')),'prototype':inter(r(p+'spa.18k'),r(p+'spa.22k'))+inter(r(p+'spa.17k'),r(p+'spa.21k'))}.items():
    put('cpu/'+name+'/m68000.bin',b);m['vectors'][name]=[f'{v:08x}' for v in struct.unpack('>64I',b[:256])]
for name,b in [('us/z80',r('a-u14.3')),('prototype/z80',r(p+'spa.17g')),('prototype/extra_z80',r(p+'6204_6-6.29c'))]:put('cpu/'+name+'.bin',b)
regions={
'release/fg':(inter(r('b-u98'),r('b-u99')),'fg'),
'release/bg':(r('b-u104')+r('b-u105'),'bg'),
'release/sprites':(inter(r('b-u110'),r('b-u111')),'sprite'),
'prototype/fg':(inter(r(p+'spa_back0_split0_5-17-p-1.27b'),r(p+'spa_back0_split1_5-17-p-1.27c')),'fg'),
'prototype/bg':(inter(r(p+'spa_back1_split0_3-14-a-11.26b'),r(p+'spa_back1_split1_3-14-a-11.26c')),'fg'),
'prototype/sprites':(r(p+'spa_sp0_4-18-p-8.5m')+r(p+'spa_sp1_3-14-a-10.4m'),'sprite'),
'prototype/extra':(r(p+'spa.25c'),'sprite')}
pal=[v for i in range(16) for v in (i*17,)*3]+[0]*720
for name,(b,mode) in regions.items():
    put('regions/'+name+'.bin',b)
    w=8 if mode=='sprite' else 16;stride=32 if mode in ('sprite','bg') else 64
    n=len(b)//(2*stride if mode=='bg' else stride);half=len(b)//2;pix=bytearray(n*w*8)
    for i in range(n):
        for y in range(8):
            for x in range(w):
                if mode=='bg':
                    k=x%8;off=(half if k%4<2 else 0)+i*32+(x//8)*16+y*2+k//4;v=b[off]&15 if k%2==0 else b[off]>>4;v=int(f'{v:04b}'[::-1],2)
                else:
                    off=i*stride+(x//8)*32+y*4+(x%8)//2;v=b[off]>>4 if x%2==0 else b[off]&15
                pix[(i*8+y)*w+x]=v
    put('graphics/'+name+'/pixels.idx',pix);dest=out/'graphics'/name
    for start in range(0,n,1024):
        count=min(n-start,1024);im=Image.new('P',(32*w,math.ceil(count/32)*8));im.putpalette(pal)
        for j in range(count):
            i=start+j;t=Image.frombytes('P',(w,8),bytes(pix[i*w*8:(i+1)*w*8]));t.putpalette(pal);im.paste(t,((j%32)*w,(j//32)*8))
        im.save(dest/f'atlas_{start:05d}.png',transparency=0)
    m['graphics'][name]=dict(width=w,height=8,count=n,columns=32,palette='diagnostic grayscale',prototype_bg_uncertain=name=='prototype/bg')
b=r('a-u19');put('audio/oki.bin',b);rate=round(1000000/132)
steps=[16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,130,143,157,173,190,209,230,253,279,307,337,371,408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552]
for i in range(128):
    a=int.from_bytes(b[i*8:i*8+3],'big')&0x3ffff;e=int.from_bytes(b[i*8+3:i*8+6],'big')&0x3ffff
    if not 1024<=a<e<len(b):continue
    sig=-2;k=0;pcm=bytearray()
    for v in b[a:e+1]:
        for c in (v>>4,v&15):
            s=steps[k];d=(s>>3)+(s>>2 if c&1 else 0)+(s>>1 if c&2 else 0)+(s if c&4 else 0)
            sig=max(-2048,min(2047,sig+(-d if c&8 else d)));k=max(0,min(48,k+[-1,-1,-1,-1,2,4,6,8][c&7]));pcm+=struct.pack('<h',sig*16)
    with wave.open(str(out/'audio'/f'sample_{i:03d}.wav'),'wb') as f:f.setparams((1,2,rate,0,'NONE',''));f.writeframes(pcm)
    m['samples'].append(dict(id=i,start=a,end=e,frames=len(pcm)//2,rate=rate))
put('manifest.json',json.dumps(m,indent=2).encode())
print('Complete:',len(m['files']), 'ROM files;',sum(v['count'] for v in m['graphics'].values()),'tiles;',len(m['samples']),'sample entries')
