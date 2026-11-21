#!/usr/bin/env python3
"""Verify course tables against the locally supplied shangon ZIP (no ROM distributed)."""
import sys, zipfile, struct, hashlib, json, re, zlib, pathlib
with zipfile.ZipFile(sys.argv[1]) as z:
    def pair(a,b):
        return bytes(x for p in zip(z.read(a),z.read(b)) for x in p)
    main=pair('epr-10886.133','epr-10884.118')+pair('epr-10887.132','epr-10885.117')
assert hashlib.sha256(main).hexdigest()=='e4f6aab7c9ab4ed3402a0adefd2b01cb3de5c32ee22c0bdc88b7b6ecf8bef2d1'
blocks=[]
blob=b''
for i in range(24):
    h=struct.unpack_from('>I',main,0x8aec+4*i)[0]
    ptr=struct.unpack_from('>9I',main,h)
    assert main[ptr[7]-2:ptr[7]]==b'\xff\xff'
    records=main[ptr[6]:ptr[7]-2]
    blob+=records
    blocks.append([list(t) for t in struct.iter_unpack('>3H',records)])
assert len(blob)==3786 and zlib.crc32(blob)==0x2525c975
lengths=[3,5,7,9]
seq=[list(struct.unpack_from('>'+str(n)+'H',main,0x8b4c+18*i)) for i,n in enumerate(lengths)]
data=(pathlib.Path(__file__).resolve().parents[1]/'data/courses.js').read_text()
assert blocks==json.loads(re.search(r'const courseBlocks=(.*);',data)[1])
assert seq==json.loads(re.search(r'const courseSequences=(.*);',data)[1])
print('PASS: 24 blocks, 631 records, 4 sequences')
