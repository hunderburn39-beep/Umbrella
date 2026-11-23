"""Read-only MegaDrive-NX VDP handshake trace analysis, v5.7.

A sampled transition is NOT necessarily a completed bus transaction.
"""
import argparse
from collections import Counter

FIELDS = ('clock','addr','data','cpu_as','cpu_rw','board_dtack','vdp_sel','vdp_ack','reg_disp','reg_m5')

def parse(path):
    with open(path, encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    if len(lines) < 3 or tuple(lines[1].split()) != FIELDS:
        raise ValueError('Unexpected trace header')
    rows=[]
    for line in lines[2:]:
        parts=line.split()
        if len(parts)!=len(FIELDS):
            raise ValueError('Malformed sample: '+line)
        r=dict(zip(FIELDS, (int(v,16) if k in ('addr','data') else int(v) for k,v in zip(FIELDS,parts))))
        if rows and r['clock']<=rows[-1]['clock']:
            raise ValueError('Clock not strictly increasing')
        if any(r[k] not in (0,1) for k in FIELDS[3:]):
            raise ValueError('Invalid binary signal')
        rows.append(r)
    return rows

def analyze(path):
    rows=parse(path)
    candidates=[]
    for i,r in enumerate(rows):
        if r['vdp_sel'] and (i==0 or r['data']!=rows[i-1]['data']):
            candidates.append((r['clock'],r['data']))
    registers=[(clock,(word>>8)&31,word&255) for clock,word in candidates if (word&0xE000)==0x8000]
    reg1=[(clock,val) for clock,reg,val in registers if reg==1]
    def falls(name):
        return sum(a[name]==1 and b[name]==0 for a,b in zip(rows,rows[1:]))
    print('Samples:',len(rows),'clocks:',rows[0]['clock'],'to',rows[-1]['clock'])
    print('Addresses:',{hex(a):n for a,n in Counter(r['addr'] for r in rows).items()})
    print('VDP ACK falling edges:',falls('vdp_ack'))
    print('Board DTACK falling edges:',falls('board_dtack'))
    print('Candidate register commands:',len(registers))
    print('Register 1 commands:',[(c,hex(v)) for c,v in reg1])
    print('Display-enable command observed:',any(v&0x40 for _,v in reg1))
    print('Display signal ever enabled:',any(r['reg_disp'] for r in rows))
    print('M5 signal ever enabled:',any(r['reg_m5'] for r in rows))
    print('Last candidate:',hex(candidates[-1][1]) if candidates else 'none')
    print('NOTE: transitions are samples, not completed transactions; no PC or pixel data.')
    return rows,registers

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('trace');analyze(p.parse_args().trace)
