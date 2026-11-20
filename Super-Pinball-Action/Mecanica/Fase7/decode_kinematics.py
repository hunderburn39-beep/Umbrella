#!/usr/bin/env python3
import json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent.parent))
from decode_motion import decode as decode_motion
def decode(raw):
 d=decode_motion(raw)
 checks={0x2c52:'41f90004010243f90004013845f90004014047f90004017848d00e00',0x5a2:'4cd00e0049d24bd3700527216a000006449301c751c8fff44cd1003fe680e681e682e683e684e685d19cd39c47d4d59cd79cd99cdb9c',0x62a:'424751ceff7408c7001f484731074e75',0x7da:'7202243c00003317',0x806:'303b00064efb0002',0x8b6:'36bc11f4377c102c0004429242aa0004',0x954:'70e260000156',0xab2:'4bfa050c103500004400488034804203d592',0xb18:'0480100010102400e6484842e84aeb48d042'}
 for a,h in checks.items():assert raw[a:a+len(bytes.fromhex(h))]==bytes.fromhex(h),hex(a)
 d.update(dict(dispatch=[0x80e+x for x in struct.unpack_from('>25h',raw,0x80e)],launch_table=list(raw[0xfc0:0x10c0]),acceleration=0x3317,substeps=8,initial_words=[0x11f4,0x102c],address_state=0x40110,address_velocity=0x40120,address_position=0x40140,address_abs_velocity=0x40160))
 assert len(d['launch_table'])==256 and d['launch_table'][0xe2]==26
 assert d['dispatch'][0]==0x840 and d['dispatch'][-1]==0xf94
 return d
if __name__=='__main__':
 d=decode(Path(sys.argv[1]).read_bytes())
 Path(sys.argv[2]).write_text(json.dumps(d,separators=(',',':')))
 print('Verified ROM signatures, 25 dispatch entries, 256 launch values, 8 substeps.')
