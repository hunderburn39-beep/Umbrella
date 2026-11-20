#!/usr/bin/env python3
"""Static extraction of US flipper tables; no CPU interpreter."""
import hashlib, struct, zipfile, json, sys
from pathlib import Path
def decode(b):
 sha=hashlib.sha256(b).hexdigest()
 assert sha=='8c139defd9b807c15872aee7e51a1fc57c8c1e4c20c764fa213d575140ca67c7'
 for start,end,h in [(0x124c,0x12da,'fc54785c26cc925dd0e583b4d329b73a76264bcc8b1c8f642654a665504b7536'),(0x136a,0x14d6,'fe50cf86fa25d7328cd46c35376dcb0530efce9ffc08428546a1f248caf1bb53'),(0x63a,0x6bc,'40adb288a34f4c0d16c42666b33fea9787b32896285cab400dc9363d10540f46'),(0x11c6,0x1236,'5baa687008f890e0263e469824c8e28494326d456493159c9fc5357df6f7631d')]:
  assert hashlib.sha256(b[start:end]).hexdigest()==h
 rows=[]
 for i in range(8):
  a=0x12da+18*i;x,y,*frames=struct.unpack_from('>9H',b,a)
  assert all(t%32==0 and t+31<16384 for t in frames)
  rows.append(dict(selector=i+1,address=a,x=x,y=y,channel=i%2,frames=frames))
 assert b[0x1e98:0x1ea0].hex()=='243b500e05c90215'
 maps=[[x for x in b[0x1ea8+i*4:0x1eac+i*4] if x] for i in range(4)]
 assert maps==[[1,2,5,6],[1,2,3,4],[1,2],[1,2,8]]
 tables={name:list(struct.unpack_from('>22I',b,a)) for name,a in [('distance',0x964e),('coefficient_a',0x96a6),('coefficient_b',0x96fe),('coefficient_c',0x9756)]}
 return dict(sha256=sha,rows=rows,maps=maps,limit=0x6ffff,tables=tables)
def rom_from_zip(path):
 with zipfile.ZipFile(path) as z:
  a,b=z.read('rom1.bin'),z.read('rom2.bin')
 raw=bytearray(len(a)*2);raw[::2]=a;raw[1::2]=b;return bytes(raw)
if __name__=='__main__':
 d=decode(rom_from_zip(sys.argv[1]));Path(sys.argv[2]).write_text(json.dumps(d,indent=2));print('8 groups, 56 frame references, 4 selector lists, 88 table words')
