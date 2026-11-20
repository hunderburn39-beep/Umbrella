#!/usr/bin/env python3
"""Reconstruct initial US tile maps. python maps.py extracted results"""
import sys, struct, json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
b=(root/'cpu/us/m68000.bin').read_bytes()
u=lambda a:struct.unpack_from('>H',b,a)[0]
l=lambda a:struct.unpack_from('>I',b,a)[0]
assert b[0x1512:0x1528].hex()=='47f9000740007c0041fa00ba3039000408021c300000'
assert b[0x1542:0x1558].hex()=='101a720f1a19da0038c551c9fff849ec006051caffe8'
assert b[0x1580:0x159a].hex()=='41f900031bdc45f90007000043ea0100103b0044c0fc0380d1c0'
assert b[0x15da:0x15ee].hex()=='41f90002fb5e45f90006410034300000d0c22258'
assert b[0x15f2:0x1604].hex()=='281842450504670000043a1934c551cafff2'
ys=b[0x15b6:0x15c6];xs=b[0x15c6:0x15d6];selector=b[0x15d6:0x15da]
gfx={k:np.frombuffer((root/'graphics/release'/k/'pixels.idx').read_bytes(),dtype=np.uint8).reshape(-1,8,16) for k in ('bg','fg')}
pal=np.array([struct.unpack_from('>2048H',b,0x34cf6+i*4096) for i in range(4)],dtype=np.uint16)
report={'source_sha256':hashlib.sha256(b).hexdigest(),'visible_unrotated':[512,224],'rotation':'90 degrees clockwise','maps':[],'note':'Static maps, no live palette selection, sprites or gameplay.'}
def col(q):return np.stack([(q&15)*17,((q>>4)&15)*17,((q>>8)&15)*17],axis=-1).astype(np.uint16)
def render(p):return Image.fromarray(p.transpose(0,2,1,3,4).reshape(224,512,p.shape[-1]).astype(np.uint8)).transpose(Image.Transpose.ROTATE_270)
for i,s in enumerate(selector):
    bg=np.zeros((32,32),dtype=np.uint16);fg=bg.copy();ba=bg.copy();fa=bg.copy()
    for y in range(32):
        for x in range(32):bg[y,x]=(s<<10)+256*(2*(x//16)+y//16)+ys[y%16]+xs[x%16]
    bap=0x31bdc+s*896;ba[2:30]=np.frombuffer(b[bap:bap+896],dtype=np.uint8).reshape(28,32)
    fbase=0x2fb5e+u(0x2fb5e+i*2);fp=l(fbase);start=fp;mask=fbase+4
    for y in range(2,30):
        bits=l(mask+(y-2)*4)
        for x in range(32):
            if bits&(1<<(31-x)):fg[y,x]=u(fp);fp+=2
    fap=0x2fb56+u(0x2fb56+i*2);fa[2:30]=np.frombuffer(b[fap:fap+896],dtype=np.uint8).reshape(28,32)
    assert len(set(bg.ravel().tolist()))==1024
    assert bg.max()<len(gfx['bg']) and fg.max()<len(gfx['fg'])
    assert fp==[0x30912,0x2ff52,0x303e8,0x30ddc][i]
    d=out/f'map_{i}';d.mkdir(exist_ok=True)
    for k,a in [('bg_tiles',bg),('bg_attrs',ba),('fg_tiles',fg),('fg_attrs',fa)]:
        (d/f'{k}.json').write_text(json.dumps(a.tolist()))
        (d/f'{k}.bin').write_bytes(a.astype('>u2').tobytes())
    bp=gfx['bg'][bg[2:30]];fpix=gfx['fg'][fg[2:30]]
    bi=(ba[2:30]>>4)[:,:,None,None]*16+bp;fi=(fa[2:30]>>4)[:,:,None,None]*16+fpix
    for bank in [None,0,1,2,3]:
        tag='indices' if bank is None else f'palette{bank}'
        for region,pix,idx,offset in [('background',bp,bi,0x200),('foreground',fpix,fi,0x100)]:
            rgb=np.repeat((pix*17)[...,None],3,axis=-1) if bank is None else col(pal[bank][offset+idx])
            img=render(np.concatenate([rgb,((pix!=0)*255)[...,None]],axis=-1))
            img.save(d/f'{region}_{tag}.png')
        with Image.open(d/f'background_{tag}.png') as g, Image.open(d/f'foreground_{tag}.png') as f:
            Image.alpha_composite(g,f).save(d/f'combined_{tag}.png')
        if bank is not None:
            z=np.where(bp!=0,bi,0)
            base=col(pal[bank][0x200+z]);solid=col(pal[bank][0x100+fi])
            blend=np.minimum(255,col(pal[bank][0x500+fi])+col(pal[bank][0x300+z]))
            useblend=((fa[2:30]&8)!=0)[:,:,None,None,None]
            mix=np.where((fpix!=0)[...,None],np.where(useblend,blend,solid),base)
            render(mix).save(d/f'mixed_palette{bank}.png')
    report['maps'].append({'level_index':i,'bg_selector':s,'bg_attr_address':hex(bap),'fg_attr_address':hex(fap),'fg_mask_address':hex(mask),'fg_stream_start':hex(start),'fg_stream_end_exclusive':hex(fp),'fg_words_read':(fp-start)//2})
assert sum(m['fg_words_read'] for m in report['maps'])==2131
(out/'maps.json').write_text(json.dumps(report,indent=2))
