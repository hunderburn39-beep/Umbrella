#!/usr/bin/env python3
import sys,zipfile,struct,hashlib,json,re,zlib,pathlib
with zipfile.ZipFile(sys.argv[1]) as z:
    def pair(a,b): return bytes(x for p in zip(z.read(a),z.read(b)) for x in p)
    m=pair('epr-10886.133','epr-10884.118')+pair('epr-10887.132','epr-10885.117')
assert hashlib.sha256(m).hexdigest()=='e4f6aab7c9ab4ed3402a0adefd2b01cb3de5c32ee22c0bdc88b7b6ecf8bef2d1'
H=[];O=[];hb=b'';ob=b''
for i in range(24):
    p=struct.unpack_from('>9I',m,struct.unpack_from('>I',m,0x8aec+4*i)[0])
    assert m[p[8]-2:p[8]]==b'\x7f\xff'
    raw=m[p[7]:p[8]-2];hb+=raw;H.append([list(v) for v in struct.iter_unpack('>4H',raw)])
    x=p[8]
    while m[x:x+2]!=b'\xff\xff':
        x+=4
        assert x<len(m)-4
    raw=m[p[8]:x];ob+=raw;O.append([list(v) for v in struct.iter_unpack('>2H',raw)])
assert len(hb)==824 and zlib.crc32(hb)==0x7022c134
assert len(ob)==5132 and zlib.crc32(ob)==0x1356ed03
data=(pathlib.Path(__file__).resolve().parents[1]/'data/course-events.js').read_text()
assert H==json.loads(re.search(r'const heightEvents=(.*);',data)[1])
assert O==json.loads(re.search(r'const objectEvents=(.*);',data)[1])
print('PASS: 103 height records, 1283 object records, original order and fields')
