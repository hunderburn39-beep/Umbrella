#!/usr/bin/env python3
import hashlib, json, struct, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent.parent/'Fase8'))
sys.path.insert(0,str(Path(__file__).parent.parent/'Fase9'))
from decode import rom_from_zip
from decode9 import decode9

def decode10(raw):
 d=decode9(raw)
 base=0x840e
 dispatch=[base+x for x in struct.unpack_from('>9h',raw,base)]
 assert dispatch==[0x8420,0x8420,0x8560,0x8852,0x8b3e,0x8b3e,0x8baa,0x8baa,0x8c1a]
 for a,h in {0x8420:'2001b25d55c24842b25d52c24a82',0x8432:'221d5bc548413401c5c0484185c1d45dd442',0x8446:'3e2bfffc044710009e42',0x8b3e:'20014841b25d55c24842b25d52c24a82',0x8baa:'2001b25d55c24842b25d52c24a82',0x8c1a:'2001b25d6500f77ab25d6200f7744841b25d6500f76cb25d6200f766'}.items():
  assert raw[a:a+len(bytes.fromhex(h))]==bytes.fromhex(h),hex(a)
 d['narrowDispatch']=dispatch
 d['narrowSupported']=[0,1,4,5,6,7,8]
 d['narrowHashes']={hex(a):hashlib.sha256(raw[a:b]).hexdigest() for a,b in [(0x8420,0x8474),(0x8b3e,0x8baa),(0x8baa,0x8c1a),(0x8c1a,0x8c78)]}
 return d
if __name__=='__main__':
 d=decode10(rom_from_zip(sys.argv[1]));Path(sys.argv[2]).write_text(json.dumps(d,separators=(',',':')))
 print(d['narrowHashes'])
