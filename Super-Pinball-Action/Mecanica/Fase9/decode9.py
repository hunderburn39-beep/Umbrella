#!/usr/bin/env python3
import struct,json,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent.parent/'Fase8'))
from decode import decode,rom_from_zip

def decode9(raw):
 d=decode(raw);u=lambda p:struct.unpack_from('>H',raw,p)[0];l=lambda p:struct.unpack_from('>I',raw,p)[0]
 assert raw[0x2c76:0x2c7e].hex()=='217c4aab2ccd0202'
 d['upStep']=0x4aab;d['downStep']=0x2ccd
 d['routineHashes']={hex(a):hashlib.sha256(raw[a:b]).hexdigest() for a,b in [(0x400,0x430),(0x6bc,0x7ac),(0x82f6,0x83fa),(0x10c0,0x113e)]}
 base=0x1804a;d['dynamicBases']=[l(0x1f1c8+4*i) for i in range(3)];assert d['dynamicBases']==[0x1f1d4,0x1f5d4,0x1f9d4]
 d['surfaces']=[];addresses=set();listcount=0;recordcount=0
 for difficulty in range(4):
  block=base+u(base+difficulty*2);maps=[]
  for j in range(4):
   geom,normal,nlist,alt,alist=struct.unpack_from('>5I',raw,block+j*20);paths=[]
   for grid,ptr in [(normal,nlist),(alt,alist)]:
    cells=list(raw[grid:grid+896]);lists=[];assert len(cells)==896
    for k in range(max(cells)):
     a=ptr+u(ptr+2*k);ws=[]
     while (w:=u(a)):
      a+=2;ws.append(w);assert len(ws)<=7
      if w&0x8000:
       b=d['dynamicBases'][(w>>8)&15]+(w&15)*128
       for frame in range(7): addresses.add(b+frame*16)
      else: addresses.add(geom+16*(w-1))
     lists.append(ws);listcount+=1;recordcount+=len(ws)
    paths.append(dict(geometry=geom,gridAddress=grid,listAddress=ptr,cells=cells,lists=lists))
   maps.append(paths)
  d['surfaces'].append(maps)
 d['surfaceRecords']={str(a):list(struct.unpack_from('>8H',raw,a)) for a in sorted(addresses)}
 d['surfaceStats']={'lists':listcount,'references':recordcount,'uniqueRecords':len(addresses),'gridEntries':32*896}
 return d
if __name__=='__main__':
 d=decode9(rom_from_zip(sys.argv[1]));Path(sys.argv[2]).write_text(json.dumps(d,separators=(',',':')));print(d['surfaceStats'],d['routineHashes'])
