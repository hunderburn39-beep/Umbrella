#!/usr/bin/env python3
"""After ../extract.py, run: python export_sprites.py extracted Sprites.zip"""
import sys,json,io,csv,hashlib,zipfile,struct
from pathlib import Path
from PIL import Image
root=Path(sys.argv[1]);target=Path(sys.argv[2]);manifest=json.loads((root/'manifest.json').read_text())
palette=[v for i in range(16) for v in (17*i,)*3];rows=[];stats={}
def code(x,y):return sum((((x>>i)&1)<<(2*i))|(((y>>i)&1)<<(2*i+1)) for i in range(3))
def emit(z,region,base,raw,w,h):
    path=f'Sprites/{region}/{w}x{h}/{base//1024*1024:05d}/{base:05d}.png'
    im=Image.frombytes('P',(w,h),raw);im.putpalette(palette);buf=io.BytesIO();im.save(buf,format='PNG',bits=4,transparency=0)
    z.writestr(path,buf.getvalue());rows.append((path,region,base,w,h,int(not any(raw)),hashlib.sha256(raw).hexdigest()))
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
    for region,info in manifest['graphics'].items():
        w,h,n=(info[k] for k in ('width','height','count'));raw=(root/'graphics'/region/'pixels.idx').read_bytes();stride=w*h
        assert len(raw)==stride*n and max(raw)<=15
        stat=stats[region]={'cells':n,'nonempty':0,'composites':{}}
        for i in range(n):
            p=raw[i*stride:(i+1)*stride];stat['nonempty']+=bool(any(p));emit(z,region,i,p,w,h)
        for f in sorted((root/'graphics'/region).glob('atlas_*.png')):z.write(f,f'Sprites/{region}/atlases/{f.name}')
        if region.endswith('/sprites'):
            for dim in (2,4,8):
                size=dim*8;group=dim*dim;st=stat['composites'][str(size)]={'count':n//group,'nonempty':0}
                for base in range(0,n,group):
                    p=bytearray(size*size)
                    for y in range(dim):
                        for x in range(dim):
                            t=base+code(x,y);tile=raw[t*64:(t+1)*64]
                            for r in range(8):
                                j=(y*8+r)*size+x*8;p[j:j+8]=tile[r*8:r*8+8]
                    st['nonempty']+=bool(any(p));emit(z,region,base,bytes(p),size,size)
    banks={}
    for version,base in [('us',0x34cf6),('jp',0x34c70)]:
        b=(root/'cpu'/version/'m68000.bin').read_bytes();banks[version]=[]
        for i in range(4):
            words=struct.unpack_from('>2048H',b,base+i*4096)
            rgb=[[(v&15)*17,((v>>4)&15)*17,((v>>8)&15)*17] for v in words]
            banks[version].append({'source':hex(base+i*4096),'words':words,'rgb':rgb,'groups':128})
            im=Image.new('RGB',(256,1024))
            for g in range(128):
                for k in range(16):im.paste(tuple(rgb[g*16+k]),(k*16,g*8,k*16+16,g*8+8))
            buf=io.BytesIO();im.save(buf,format='PNG');z.writestr(f'Sprites/palettes/palette_{version}_{i}.png',buf.getvalue())
    z.writestr('Sprites/palettes/banks.json',json.dumps(banks,separators=(',',':')))
    s=io.StringIO();writer=csv.writer(s,lineterminator='\n');writer.writerow(['path','region','base_tile_id','width','height','blank','sha256_pen_indices']);writer.writerows(rows);z.writestr('Sprites/catalog.csv',s.getvalue())
    z.writestr('Sprites/manifest.json',json.dumps({'total_individual_png':len(rows),'regions':stats,'palette':'diagnostic grayscale, original pen indices preserved','composites':'possible aligned squares, not verified distinct objects','prototype_bg_uncertain':True},indent=2))
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    for row in rows:
        with Image.open(io.BytesIO(z.read(row[0]))) as im:
            assert im.mode=='P' and im.size==(row[3],row[4]) and hashlib.sha256(im.tobytes()).hexdigest()==row[6]
print('Verified',len(rows),'individual PNG files.')
