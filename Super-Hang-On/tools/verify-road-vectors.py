#!/usr/bin/env python3
"""Cross-check main-CPU radius and direction against sub-CPU original vectors."""
import hashlib, json, math, pathlib, re, statistics, struct, sys, zipfile, zlib
with zipfile.ZipFile(sys.argv[1]) as z:
    def pair(a,b): return bytes(x for t in zip(z.read(a),z.read(b)) for x in t)
    m=pair('epr-10886.133','epr-10884.118')+pair('epr-10887.132','epr-10885.117')
    s=pair('epr-10792.76','epr-10790.58')+pair('epr-10793.75','epr-10791.57')
assert hashlib.sha256(m).hexdigest()=='e4f6aab7c9ab4ed3402a0adefd2b01cb3de5c32ee22c0bdc88b7b6ecf8bef2d1'
assert hashlib.sha256(s).hexdigest()=='770332456d5c438c8e4741b9a386e1ba8c4c2c35b59391f04609b75f9e1109a5'
ptr=struct.unpack_from('>24I',s,0x19e8)
raw=b''.join(s[p:p+8192] for p in ptr)
assert len(raw)==196608 and zlib.crc32(raw)==0x8429338f
assert hashlib.sha256(raw).hexdigest()=='bb50d4287274b44cb28fb10268272a88af6483130a3e93acc1e50185e0e0138d'
blocks=json.loads(re.search(r'const courseBlocks=(.*);',(pathlib.Path(__file__).resolve().parents[1]/'data/courses.js').read_text())[1])
counts=[0,0,0,0,0]
all_vectors=[]
for b,p in enumerate(ptr):
    v=list(struct.iter_unpack('>hh',s[p:p+8192])); all_vectors.append(v)
    h=struct.unpack_from('>I',m,0x8aec+b*4)[0]
    q=struct.unpack_from('>9I',m,h)
    r=list(struct.iter_unpack('>HHH',m[q[6]:q[7]-2]))
    assert [list(x) for x in r]==blocks[b]
    for i,(st,rad,t) in enumerate(r):
        end=r[i+1][0] if i+1<len(r) else 2048
        vals=[math.atan2(y*nx-x*ny,x*nx+y*ny) for (x,y),(nx,ny) in zip(v[st+2:end-2],v[st+3:end-1]) if 3500<math.hypot(x,y)<4300 and 3500<math.hypot(nx,ny)<4300]
        med=statistics.median(vals)
        if t==1:
            counts[0]+=1; counts[1]+=abs(med)<.001
        else:
            sign=1 if t==2 else -1
            counts[2]+=1; counts[3]+=med*sign>0; counts[4]+=abs(med*sign*rad-1)<.05
assert counts==[208,208,423,423,422],counts
print('PASS: 49152 vectors; 208 straights; 423 directions; 422 inverse radii within 5%')
if len(sys.argv)>2:
    pathlib.Path(sys.argv[2]).write_text(json.dumps({'source':'sub68k','pointerTable':'0x19E8','scale':4096,'vectors':all_vectors},separators=(',',':')))
