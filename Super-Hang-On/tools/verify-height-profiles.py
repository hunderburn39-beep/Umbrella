#!/usr/bin/env python3
import sys,zipfile,struct,hashlib,zlib,json,re,pathlib
with zipfile.ZipFile(sys.argv[1]) as z:
    def pair(a,b): return bytes(x for t in zip(z.read(a),z.read(b)) for x in t)
    s=pair('epr-10792.76','epr-10790.58')+pair('epr-10793.75','epr-10791.57')
assert hashlib.sha256(s).hexdigest()=='770332456d5c438c8e4741b9a386e1ba8c4c2c35b59391f04609b75f9e1109a5'
ptr=struct.unpack_from('>21I',s,0x1a48)
profiles=[];raw=b''
for i,p in enumerate(ptr):
    vectors=[]
    while p+4<=len(s):
        x,y=struct.unpack_from('>hh',s,p)
        if (x,y)==(0,0): break
        vectors.append([x,y]);raw+=s[p:p+4];p+=4
    else: raise ValueError('Missing terminator')
    profiles.append({'id':i+1,'address':hex(ptr[i]),'vectors':vectors})
assert len(raw)==30800 and zlib.crc32(raw)==0x66db5b8b
assert hashlib.sha256(raw).hexdigest()=='b32c3aeaaccd77c739ea88b388e2ddba8693cd235622179417f28e3f4ed38821'
sample=[[len(p['vectors']),[v[0] for v in p['vectors'][::16]]+[0]] for p in profiles]
source=(pathlib.Path(__file__).resolve().parents[1]/'data/height-profiles.js').read_text()
assert sample==json.loads(re.search(r'const heightProfileSamples=(.*);',source)[1])
if len(sys.argv)>2: pathlib.Path(sys.argv[2]).write_text(json.dumps({'pointerTable':'0x1A48','codeReference':'0x1602','scale':4096,'rawCRC32':'66db5b8b','profiles':profiles},separators=(',',':')))
print('PASS: 21 profiles, 7700 vectors and all browser samples')
