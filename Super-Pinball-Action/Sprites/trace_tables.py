#!/usr/bin/env python3
"""Static table decoder for the US Super Pinball Action ROM."""
import sys,struct,json,hashlib
from pathlib import Path
b=Path(sys.argv[1]).read_bytes()
u=lambda a:struct.unpack_from('>H',b,a)[0]
s=lambda a:struct.unpack_from('>h',b,a)[0]
assert b[0xc8e2:0xc8ea].hex()=='49fa0518d8f40000'
assert b[0xca5e:0xca66].hex()=='47fa089e32330000'
assert b[0xc90a:0xc91e].hex()=='101c6b00001ce948024000f034801a1c35454000'
assert b[0xca7a:0xca86].hex()=='30fc002430c130c030c230c3'
base=0xcdfc; count=u(base)//2;assert count==50
fragments=[]
for i in range(count):
    addr=base+s(base+2*i);p=addr;offset=0;x=y=anchor_y=0;parts=[];commands=[]
    while True:
        c=b[p];p+=1
        if c==255:break
        if c<128:
            t=offset|b[p];p+=1;assert t<8192;parts.append({'x':x,'y':y,'tile':t,'color_group':c&15});y-=1
        elif c&3==0:offset|=b[p]<<8;p+=1;commands.append([c,offset])
        elif c&3==1:
            dx=b[p]&31;dy=int.from_bytes(b[p+1:p+2],'big',signed=True);p+=2;x+=dx;anchor_y+=dy;y=anchor_y;commands.append([c,dx,dy])
        else:commands.append([c])
        assert p-addr<1024
    fragments.append({'id':i,'address':hex(addr),'end':hex(p),'commands':commands,'tiles':parts})
groups=[];p=0xcdb4
while p<base:
    a=p;items=[]
    while u(p)!=0xffff:
        i=u(p);anchor=u(p+2);p+=4;assert i<count;items.append({'fragment':i,'x':anchor&31,'y':(anchor>>8)&31})
    p+=2;groups.append({'address':hex(a),'items':items})
assert p==base and len(groups)==8
strips=[]
for i,a in enumerate(range(0xd2fe,0xd3ac,2)):
    word=u(a);n=0x2000|(word&0xfff);g=word>>12;assert n+7<16384 and n%4==0
    strips.append({'id':i,'address':hex(a),'word':hex(word),'base_tile':n,'second_tile':n+4,'color_group':g})
seqs=[];coords=list(zip(b[0xcaa4:0xcaea:2],b[0xcaa5:0xcaea:2]));assert len(coords)==35
for i in range(4):
    a=0xd190+u(0xd190+4*i);d=0xd190+u(0xd192+4*i);p=a;j=0;events=[];slot=0
    while True:
        c=b[p];p+=1;delay=b[d+j];j+=1
        if c==255:break
        if c==128:events.append({'op':'clear','delay_counter':delay});slot=0;continue
        assert c<len(strips) and slot<len(coords),(i,c,slot)
        y,x=coords[slot];events.append({'op':'draw_pair','id':c,'x':x,'y':y,'delay_counter':delay,'slot':slot});slot+=1
    seqs.append({'id':i,'script_address':hex(a),'delay_address':hex(d),'events':events})
assert sum(len(x['tiles']) for x in fragments)==253
assert len(strips)==87 and sum(len(x['events']) for x in seqs)==153
Path(sys.argv[2]).write_text(json.dumps({'source_sha256':hashlib.sha256(b).hexdigest(),'background_fragments':fragments,'overlay_groups':groups,'sprite_strips':strips,'sequences':seqs,'flipper_candidate_base_ids':[i*64 for i in list(range(8,16))+list(range(32,40))]},indent=2))
print('50 fragments, 253 placements, 8 overlay groups, 87 pairs, 4 scripts, 153 events.')
