#!/usr/bin/env python3
"""Extract motion response tables from the US release. No CPU emulation."""
import struct, hashlib, json, sys
from pathlib import Path

def decode(raw):
    sha=hashlib.sha256(raw).hexdigest()
    assert sha=='8c139defd9b807c15872aee7e51a1fc57c8c1e4c20c764fa213d575140ca67c7'
    assert raw[0x16f0:0x1708].hex()=='43e8001045f9000900013351000270001212460108010004'
    assert raw[0xb04:0xb4e].hex()=='4bf90001deaad04030350000dac02013302b00040480100010102400e6484842e84aeb48d04274001435000030024bf90001f0400242003fd442d442d442dac2241dd5aa00042415d592'
    u=lambda p:struct.unpack_from('>H',raw,p)[0]
    base=0x1deaa
    maps=[]
    for i in range(4):
        a=base+u(base+i*2);cells=list(raw[a:a+896]);assert len(cells)==896
        maps.append(dict(id=i,address=a,cells=cells,codes=sorted(set(cells))))
    assert sorted(x['address'] for x in maps)==list(range(base+8,0x1ecb2,896))
    special_address=0x1ecb2+u(0x1ecb2+4)
    special=list(raw[special_address:0x1f03c]);assert len(special)==896
    impulses=[list(struct.unpack_from('>ii',raw,0x1f040+i*8)) for i in range(48)]
    assert max(v&63 for m in maps for v in m['cells'])<48 and max(v&63 for v in special)<48
    assert impulses[0]==[0,13078] and all(v%6539==0 or v==3269 for p in impulses for v in p)
    return dict(sha256=sha,maps=maps,special_address=special_address,special=special,impulses=impulses,grid=[32,28],pair_order=['delta_at_a2_plus_4','delta_at_a2'],note='Original bytes; visual placement and physics units are not yet dynamically confirmed.')
if __name__=='__main__':
    Path(sys.argv[2]).write_text(json.dumps(decode(Path(sys.argv[1]).read_bytes()),separators=(',',':')))
    print('Verified: 3584 primary bytes, 896 companion bytes, 48 signed impulse pairs.')
