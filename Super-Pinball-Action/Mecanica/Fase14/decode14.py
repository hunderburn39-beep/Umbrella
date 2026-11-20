#!/usr/bin/env python3
import hashlib,struct,sys,json,zipfile
from pathlib import Path

def decode14(b):
 assert hashlib.sha256(b).hexdigest()=='8c139defd9b807c15872aee7e51a1fc57c8c1e4c20c764fa213d575140ca67c7'
 u=lambda a:struct.unpack_from('>H',b,a)[0]
 base=0x17e66; scripts=[]
 for m,n in enumerate((16,18,9,14)):
  a=base+u(base+2*m); out=[]
  assert u(a+2)==(n+1)*2
  for i in range(1,n+1):
   start=a+u(a+2*i); p=start;words=[]
   while u(p)!=0xffff:
    w=u(p);p+=2; assert w>>8<=11 and (w&255)<(64 if (w>>8)%4==0 else 32)
    words.append(w)
   p+=2
   assert p==(a+u(a+2*(i+1)) if i<n else a+u(a+2)+sum((len(s['words'])+1)*2 for s in out)+(len(words)+1)*2)
   out.append({'id':i,'address':start,'end':p,'words':words})
  scripts.append(out)
 assert sum(len(x) for x in scripts)==57
 assert sorted((x[0]['address'],x[-1]['end']) for x in scripts)==[(0x17e94,0x17efc),(0x17f10,0x17f4c),(0x17f6e,0x17fca),(0x17fe8,0x1804a)]
 cb={}
 for t,base,n in [('slope',0x97ce,19),('curve',0xa1f4,10),('horizontal',0xa700,4),('vertical',0xa772,16),('zone',0xab90,24)]:
  cb[t]=[base+u(base+2*j) for j in range(n)]
 states={'slope':{7:[1,2],8:[0,9]},'curve':{4:[0,9]},'horizontal':{3:[0,9]},'vertical':{3:[1,2],4:[0,9]}}
 signatures={0x9c08:'08ea0007fffc670000044e75157c0002ffff4e75',0x9c1c:'08aa0007fffc660000044e75157c0009ffff4e75',0xa642:'08aa0007fffc660000044e75157c0009ffff4e75',0xa73e:'08aa0007fffc660000044e75157c0009ffff4e75',0xa7b8:'08ea0007fffc670000044e75157c0002ffff4e75',0xa7cc:'08aa0007fffc660000044e75157c0009ffff4e75'}
 for a,h in signatures.items():assert b[a:a+len(bytes.fromhex(h))].hex()==h
 return {'eventScripts':scripts,'eventDispatch':cb,'eventStateCallbacks':states,'eventStats':{'scripts':57,'operations':sum(len(s['words']) for x in scripts for s in x),'callbacks':sum(map(len,cb.values()))},'eventHashes':{hex(a):hashlib.sha256(b[a:z]).hexdigest() for a,z in [(0x9f54,0xa1e0),(0x17e66,0x1804a)]}}
if __name__=='__main__':
 with zipfile.ZipFile(sys.argv[1]) as z:
  a,c=z.read('rom1.bin'),z.read('rom2.bin');b=bytearray(len(a)*2);b[::2]=a;b[1::2]=c
 d=decode14(b);Path(sys.argv[2]).write_text(json.dumps(d,separators=(',',':')));print(d['eventStats'])
